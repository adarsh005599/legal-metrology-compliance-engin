import re
from typing import List, Tuple, Optional, Union
from app.models import RuleResult, OCRLine
from app.engine.exemption import is_nutrition_or_ingredient_line

CONFIDENCE_THRESHOLD = 0.60

def _extract_text_and_confidences(text_or_ocr_lines: Union[List[str], List[OCRLine]]) -> Tuple[List[str], List[Optional[float]]]:
    """Helper to extract text lines and their corresponding OCR confidence scores."""
    lines: List[str] = []
    confidences: List[Optional[float]] = []
    for item in text_or_ocr_lines:
        if isinstance(item, OCRLine):
            lines.append(item.text)
            confidences.append(item.confidence)
        elif isinstance(item, str):
            lines.append(item)
            confidences.append(None)
        else:
            lines.append(str(item))
            confidences.append(None)
    return lines, confidences


def _check_confidence_status(found_conf: Optional[float], base_status: str, default_details: str) -> Tuple[str, Optional[float], str, Optional[str]]:
    """
    Evaluates OCR confidence score.
    If confidence is below 0.60, mark as 'UNCERTAIN' instead of clean PASS/WARNING.
    """
    if found_conf is not None:
        score = round(float(found_conf), 3)
        if score < CONFIDENCE_THRESHOLD:
            pct = round(score * 100, 1)
            return (
                "UNCERTAIN",
                score,
                f"Uncertain — low OCR confidence ({pct}% < 60%), manual review recommended.",
                f"Low OCR confidence ({pct}%)"
            )
        return (base_status, score, default_details, None)
    return (base_status, None, default_details, None)


def check_mrp(text_or_ocr_lines: Union[List[str], List[OCRLine]]) -> RuleResult:
    """
    Field 1: Maximum Retail Price (MRP) - Rule 6(1)(e)
    Matches 'MRP', 'M.R.P', 'Maximum Retail Price' strictly in close proximity to a rupee amount.
    Audited: Price amount MUST be on the same line or immediately adjacent to MRP keywords.
    Flags dual pricing, sticker alteration, or low OCR confidence (< 0.60).
    """
    lines, confidences = _extract_text_and_confidences(text_or_ocr_lines)
    full_text = " ".join(lines)

    # Regex matching MRP keyword with price on the same line/phrase
    # e.g., MRP Rs. 150.00, M.R.P. ₹ 99, MRP : 45.50 (incl. of all taxes), Max Retail Price Rs 200
    mrp_line_regex = re.compile(
        r"(?:m\.?r\.?p\.?|max(?:imum)?\s*retail\s*price)\s*(?:is)?\s*[:\.\s-]*\s*(?:(?:rs\.?|inr|₹)\s*)?([0-9]+(?:\.[0-9]{1,2})?)",
        re.IGNORECASE
    )

    matched_lines = []
    matched_confs = []
    detected_prices = []

    for idx, line in enumerate(lines):
        # Ignore nutrition/ingredients lines
        if is_nutrition_or_ingredient_line(line):
            continue

        match = mrp_line_regex.search(line)
        if match:
            matched_lines.append((line.strip(), match.group(0).strip()))
            matched_confs.append(confidences[idx])
            val = match.group(1)
            if val:
                try:
                    detected_prices.append(float(val))
                except ValueError:
                    pass

    # Check two consecutive lines if keyword is on line i and price on line i+1
    if not matched_lines:
        for idx in range(len(lines) - 1):
            curr_line = lines[idx].strip()
            next_line = lines[idx+1].strip()
            if is_nutrition_or_ingredient_line(curr_line) or is_nutrition_or_ingredient_line(next_line):
                continue
            if re.search(r"\b(?:m\.?r\.?p\.?|max(?:imum)?\s*retail\s*price)[:\s-]*$", curr_line, re.IGNORECASE):
                p_match = re.search(r"^(?:(?:rs\.?|inr|₹)\s*)?([0-9]+(?:\.[0-9]{1,2})?)\b", next_line, re.IGNORECASE)
                if p_match:
                    combined = f"{curr_line} {next_line}"
                    matched_lines.append((combined, combined))
                    matched_confs.append(min(c for c in [confidences[idx], confidences[idx+1]] if c is not None) if any(c is not None for c in [confidences[idx], confidences[idx+1]]) else None)
                    val = p_match.group(1)
                    if val:
                        try:
                            detected_prices.append(float(val))
                        except ValueError:
                            pass

    if not matched_lines:
        return RuleResult(
            field_id="mrp",
            field_name="Maximum Retail Price (MRP)",
            rule_reference="Rule 6(1)(e), Legal Metrology (Packaged Commodities) Rules, 2011",
            status="FAIL",
            found=False,
            matched_text=None,
            confidence_score=None,
            flag=None,
            details="No valid MRP declaration or price amount detected in proximity to required MRP keywords."
        )

    primary_text = matched_lines[0][1]
    primary_conf = matched_confs[0]
    distinct_prices = set(detected_prices)

    # Check for sticker / dual pricing anomaly
    sticker_keywords = bool(re.search(r"\b(sticker|pasted\s*price|revised\s*mrp|re-labeled|over-printed|dual\s*price)\b", full_text, re.IGNORECASE))
    has_conflicting_prices = len(distinct_prices) > 1

    if has_conflicting_prices or sticker_keywords:
        anomaly_reasons = []
        if has_conflicting_prices:
            prices_str = ", ".join(f"₹{p}" for p in sorted(distinct_prices))
            anomaly_reasons.append(f"Multiple distinct MRP amounts detected: {prices_str}")
        if sticker_keywords:
            anomaly_reasons.append("Price sticker / overprinting keyword detected")
            
        flag_msg = " ; ".join(anomaly_reasons)
        base_status = "WARNING"
        default_details = f"MRP declaration is present, but potential dual pricing or sticker alteration was flagged: {flag_msg}."
        status, conf_score, details, conf_flag = _check_confidence_status(primary_conf, base_status, default_details)
        
        flags = [f"Dual Pricing Anomaly: {flag_msg}"]
        if conf_flag:
            flags.append(conf_flag)

        return RuleResult(
            field_id="mrp",
            field_name="Maximum Retail Price (MRP)",
            rule_reference="Rule 6(1)(e), Legal Metrology (Packaged Commodities) Rules, 2011",
            status=status,
            found=True,
            matched_text=" | ".join(m[1] for m in matched_lines),
            confidence_score=conf_score,
            flag=" | ".join(flags),
            details=details
        )

    # Clean pass evaluation with confidence check
    base_status = "PASS"
    default_details = f"Compliant MRP declaration detected: '{primary_text}'."
    status, conf_score, details, conf_flag = _check_confidence_status(primary_conf, base_status, default_details)

    return RuleResult(
        field_id="mrp",
        field_name="Maximum Retail Price (MRP)",
        rule_reference="Rule 6(1)(e), Legal Metrology (Packaged Commodities) Rules, 2011",
        status=status,
        found=True,
        matched_text=primary_text,
        confidence_score=conf_score,
        flag=conf_flag,
        details=details
    )


def check_net_quantity(text_or_ocr_lines: Union[List[str], List[OCRLine]]) -> RuleResult:
    """
    Field 2: Net Quantity - Rule 6(1)(b) & Rule 12
    Must find a value in standard SI units (g, kg, ml, l).
    Audited: Excludes numbers inside nutrition/ingredient panels. Requires net quantity keywords
    or a dedicated non-nutrition quantity declaration line.
    Flags non-standard units (gm, gms, kgs, ltr, ltrs, ml.) and low confidence (< 0.60).
    """
    lines, confidences = _extract_text_and_confidences(text_or_ocr_lines)

    # 1. First look for lines with explicit Net Quantity keywords (excluding nutrition panels)
    prefix_regex = re.compile(
        r"\b(?:net\s*(?:wt|weight|qty|quantity|vol|volume|content|contents)|contains|package\s*size|pkg\s*size)[:\.\s-]+(\d+(?:\.\d+)?)\s*([a-zA-Z\.]+)",
        re.IGNORECASE
    )

    # Standard SI and non-standard unit matchers on whole line
    std_units = {"g", "kg", "ml", "l", "L"}
    non_std_units = {"gm", "gms", "kgs", "ltr", "ltrs", "ml.", "gm.", "gms.", "gram", "grams", "kilo", "kilos"}

    for idx, line in enumerate(lines):
        if is_nutrition_or_ingredient_line(line):
            continue

        match = prefix_regex.search(line)
        if match:
            val = match.group(1)
            raw_unit = match.group(2).strip().rstrip('.')
            unit_lower = raw_unit.lower()
            full_match = match.group(0).strip()
            conf = confidences[idx]

            if raw_unit in std_units or unit_lower in {"g", "kg", "ml", "l"}:
                base_status = "PASS"
                default_details = f"Standard SI net quantity declaration detected: '{full_match}'."
                status, conf_score, details, conf_flag = _check_confidence_status(conf, base_status, default_details)
                return RuleResult(
                    field_id="net_quantity",
                    field_name="Net Quantity",
                    rule_reference="Rule 6(1)(b) & Rule 12, Legal Metrology (Packaged Commodities) Rules, 2011",
                    status=status,
                    found=True,
                    matched_text=full_match,
                    confidence_score=conf_score,
                    flag=conf_flag,
                    details=details
                )
            elif unit_lower in non_std_units:
                base_status = "WARNING"
                default_details = f"Net quantity is declared as '{full_match}', but uses non-prescribed unit symbol '{raw_unit}'. Must use standard SI symbol 'g'/'kg'/'ml'/'l'."
                status, conf_score, details, conf_flag = _check_confidence_status(conf, base_status, default_details)
                flag_str = f"Non-standard unit '{raw_unit}' used. Rule 12 prescribes standard SI symbols: 'g', 'kg', 'ml', 'l'."
                if conf_flag:
                    flag_str += f" | {conf_flag}"
                return RuleResult(
                    field_id="net_quantity",
                    field_name="Net Quantity",
                    rule_reference="Rule 6(1)(b) & Rule 12, Legal Metrology (Packaged Commodities) Rules, 2011",
                    status=status,
                    found=True,
                    matched_text=full_match,
                    confidence_score=conf_score,
                    flag=flag_str,
                    details=details
                )

    # 2. Standalone quantity line check (ONLY if line is non-nutrition and contains standard quantity format)
    standalone_std = re.compile(r"^(?:(?:net\s*(?:wt|weight|qty|quantity)?[:\.\s-]*)?|\b)(\d+(?:\.\d+)?)\s*(kg|g|ml|l|L)\b", re.IGNORECASE)
    standalone_non_std = re.compile(r"^(?:(?:net\s*(?:wt|weight|qty|quantity)?[:\.\s-]*)?|\b)(\d+(?:\.\d+)?)\s*(gms?|kgs|ltrs?|m\.l\.|gm\.|gms\.)\b", re.IGNORECASE)

    for idx, line in enumerate(lines):
        if is_nutrition_or_ingredient_line(line):
            continue

        std_m = standalone_std.search(line)
        if std_m:
            matched_text = std_m.group(0).strip()
            conf = confidences[idx]
            base_status = "PASS"
            default_details = f"Net quantity detected in standard SI unit: '{matched_text}'."
            status, conf_score, details, conf_flag = _check_confidence_status(conf, base_status, default_details)
            return RuleResult(
                field_id="net_quantity",
                field_name="Net Quantity",
                rule_reference="Rule 6(1)(b) & Rule 12, Legal Metrology (Packaged Commodities) Rules, 2011",
                status=status,
                found=True,
                matched_text=matched_text,
                confidence_score=conf_score,
                flag=conf_flag,
                details=details
            )

        non_std_m = standalone_non_std.search(line)
        if non_std_m:
            matched_text = non_std_m.group(0).strip()
            unit = non_std_m.group(2)
            conf = confidences[idx]
            base_status = "WARNING"
            default_details = f"Net quantity detected as '{matched_text}' using non-standard unit notation '{unit}'."
            status, conf_score, details, conf_flag = _check_confidence_status(conf, base_status, default_details)
            flag_str = f"Non-standard unit '{unit}' used instead of standard SI symbol (Rule 12)."
            if conf_flag:
                flag_str += f" | {conf_flag}"
            return RuleResult(
                field_id="net_quantity",
                field_name="Net Quantity",
                rule_reference="Rule 6(1)(b) & Rule 12, Legal Metrology (Packaged Commodities) Rules, 2011",
                status=status,
                found=True,
                matched_text=matched_text,
                confidence_score=conf_score,
                flag=flag_str,
                details=details
            )

    return RuleResult(
        field_id="net_quantity",
        field_name="Net Quantity",
        rule_reference="Rule 6(1)(b) & Rule 12, Legal Metrology (Packaged Commodities) Rules, 2011",
        status="FAIL",
        found=False,
        matched_text=None,
        confidence_score=None,
        flag=None,
        details="No net quantity or weight/volume declaration found with required net quantity keywords."
    )


def check_mfg_date(text_or_ocr_lines: Union[List[str], List[OCRLine]]) -> RuleResult:
    """
    Field 3: Month & Year of Manufacture / Packing - Rule 6(1)(d)
    Matches date patterns strictly in proximity to 'mfg', 'mfd', 'manufactured', 'pkd', 'packed', 'pkg'.
    Audited: Date must be adjacent to mfg/pkd keywords, not an arbitrary date or batch number.
    Flags low confidence (< 0.60).
    """
    lines, confidences = _extract_text_and_confidences(text_or_ocr_lines)

    months_str = r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
    date_regex = rf"(?:(?:0?[1-9]|[12][0-9]|3[01])[\/\.-])?(?:(?:0?[1-9]|1[0-2])|{months_str})[\/\.\s,-]+(?:20[2-9][0-9]|[2-9][0-9])"

    mfg_pattern = re.compile(
        rf"(?:mfg|mfd|manufactur(?:ed|ing)|pkd|packed|pack(?:ing)?|pkg|date\s*of\s*(?:mfg|mfd|pkd|packing|manufacture))\s*[:\.\s-]*\s*({date_regex})",
        re.IGNORECASE
    )

    for idx, line in enumerate(lines):
        if is_nutrition_or_ingredient_line(line):
            continue

        match = mfg_pattern.search(line)
        if match:
            matched_text = match.group(0).strip()
            conf = confidences[idx]
            base_status = "PASS"
            default_details = f"Manufacture/Packing date declaration detected: '{matched_text}'."
            status, conf_score, details, conf_flag = _check_confidence_status(conf, base_status, default_details)
            return RuleResult(
                field_id="mfg_date",
                field_name="Month & Year of Manufacture / Packing",
                rule_reference="Rule 6(1)(d), Legal Metrology (Packaged Commodities) Rules, 2011",
                status=status,
                found=True,
                matched_text=matched_text,
                confidence_score=conf_score,
                flag=conf_flag,
                details=details
            )

        # Keyword and date on same line
        if re.search(r"\b(mfg|mfd|manufactured|pkd|packed|pkg)\b", line, re.IGNORECASE):
            d_match = re.search(date_regex, line, re.IGNORECASE)
            if d_match:
                matched_text = line.strip()
                conf = confidences[idx]
                base_status = "PASS"
                default_details = f"Manufacture/Packing date found in line: '{matched_text}'."
                status, conf_score, details, conf_flag = _check_confidence_status(conf, base_status, default_details)
                return RuleResult(
                    field_id="mfg_date",
                    field_name="Month & Year of Manufacture / Packing",
                    rule_reference="Rule 6(1)(d), Legal Metrology (Packaged Commodities) Rules, 2011",
                    status=status,
                    found=True,
                    matched_text=matched_text,
                    confidence_score=conf_score,
                    flag=conf_flag,
                    details=details
                )

    return RuleResult(
        field_id="mfg_date",
        field_name="Month & Year of Manufacture / Packing",
        rule_reference="Rule 6(1)(d), Legal Metrology (Packaged Commodities) Rules, 2011",
        status="FAIL",
        found=False,
        matched_text=None,
        confidence_score=None,
        flag=None,
        details="No Month/Year of manufacture or packing date declaration found near required keywords."
    )


def check_manufacturer_address(text_or_ocr_lines: Union[List[str], List[OCRLine]]) -> RuleResult:
    """
    Field 4: Manufacturer / Packer / Importer Name & Address - Rule 6(1)(a)
    Looks for keywords 'mfd by', 'manufactured by', 'marketed by', 'packed by', 'imported by' followed by address text.
    Flags low confidence (< 0.60).
    """
    lines, confidences = _extract_text_and_confidences(text_or_ocr_lines)

    addr_pattern = re.compile(
        r"(?:mfd\.?\s*by|manufactured\s*by|marketed\s*by|mktd\.?\s*by|packed\s*by|pkd\.?\s*by|imported\s*by|distributed\s*by|manufactured\s*&\s*packed\s*by)\s*[:\.\s-]*([^\n\r;]{5,150})",
        re.IGNORECASE
    )

    for idx, line in enumerate(lines):
        if is_nutrition_or_ingredient_line(line):
            continue

        match = addr_pattern.search(line)
        if match:
            matched_text = match.group(0).strip()
            conf = confidences[idx]
            base_status = "PASS"
            default_details = f"Manufacturer/Packer declaration detected: '{matched_text}'."
            status, conf_score, details, conf_flag = _check_confidence_status(conf, base_status, default_details)
            return RuleResult(
                field_id="address",
                field_name="Name & Address of Manufacturer / Packer / Importer",
                rule_reference="Rule 6(1)(a), Legal Metrology (Packaged Commodities) Rules, 2011",
                status=status,
                found=True,
                matched_text=matched_text,
                confidence_score=conf_score,
                flag=conf_flag,
                details=details
            )

        if re.search(r"\b(mfd\s*by|manufactured\s*by|marketed\s*by|packed\s*by|imported\s*by)\b", line, re.IGNORECASE):
            matched_text = line.strip()
            conf = confidences[idx]
            base_status = "PASS"
            default_details = f"Manufacturer/Packer line found: '{matched_text}'."
            status, conf_score, details, conf_flag = _check_confidence_status(conf, base_status, default_details)
            return RuleResult(
                field_id="address",
                field_name="Name & Address of Manufacturer / Packer / Importer",
                rule_reference="Rule 6(1)(a), Legal Metrology (Packaged Commodities) Rules, 2011",
                status=status,
                found=True,
                matched_text=matched_text,
                confidence_score=conf_score,
                flag=conf_flag,
                details=details
            )

    return RuleResult(
        field_id="address",
        field_name="Name & Address of Manufacturer / Packer / Importer",
        rule_reference="Rule 6(1)(a), Legal Metrology (Packaged Commodities) Rules, 2011",
        status="FAIL",
        found=False,
        matched_text=None,
        confidence_score=None,
        flag=None,
        details="No manufacturer, packer, or importer name and address declaration found."
    )


def check_consumer_care(text_or_ocr_lines: Union[List[str], List[OCRLine]]) -> RuleResult:
    """
    Field 5: Consumer Care Details - Rule 6(1)(f)
    Regex for a 10-digit phone number OR an email pattern (or toll-free helpline).
    Flags low confidence (< 0.60).
    """
    lines, confidences = _extract_text_and_confidences(text_or_ocr_lines)

    email_pattern = re.compile(r"\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b")
    phone_pattern = re.compile(
        r"(?:(?:\+91[\s-]*)?[6-9]\d{9}\b|1800[\s-]?\d{3}[\s-]?\d{3,4}\b|0\d{2,4}[\s-]\d{6,8}\b)",
        re.IGNORECASE
    )

    matched_elements = []
    matched_confs = []

    for idx, line in enumerate(lines):
        if is_nutrition_or_ingredient_line(line):
            continue

        e_matches = list(email_pattern.finditer(line))
        p_matches = list(phone_pattern.finditer(line))

        if e_matches or p_matches:
            for em in e_matches:
                matched_elements.append(f"Email: {em.group(0).strip()}")
                matched_confs.append(confidences[idx])
            for pm in p_matches:
                matched_elements.append(f"Phone: {pm.group(0).strip()}")
                matched_confs.append(confidences[idx])

    if matched_elements:
        valid_confs = [c for c in matched_confs if c is not None]
        min_conf = min(valid_confs) if valid_confs else None
        base_status = "PASS"
        default_details = f"Consumer Care contact details detected: {' | '.join(matched_elements)}."
        status, conf_score, details, conf_flag = _check_confidence_status(min_conf, base_status, default_details)
        return RuleResult(
            field_id="consumer_care",
            field_name="Consumer Care Details",
            rule_reference="Rule 6(1)(f), Legal Metrology (Packaged Commodities) Rules, 2011",
            status=status,
            found=True,
            matched_text=" | ".join(matched_elements),
            confidence_score=conf_score,
            flag=conf_flag,
            details=details
        )

    return RuleResult(
        field_id="consumer_care",
        field_name="Consumer Care Details",
        rule_reference="Rule 6(1)(f), Legal Metrology (Packaged Commodities) Rules, 2011",
        status="FAIL",
        found=False,
        matched_text=None,
        confidence_score=None,
        flag=None,
        details="No valid consumer care phone number (10-digit / 1800 toll-free) or email address detected on label."
    )


def evaluate_all_rules(text_or_ocr_lines: Union[List[str], List[OCRLine]]) -> List[RuleResult]:
    """
    Runs the 5 mandatory Legal Metrology declaration rule checks with confidence auditing.
    """
    return [
        check_mrp(text_or_ocr_lines),
        check_net_quantity(text_or_ocr_lines),
        check_mfg_date(text_or_ocr_lines),
        check_manufacturer_address(text_or_ocr_lines),
        check_consumer_care(text_or_ocr_lines),
    ]
