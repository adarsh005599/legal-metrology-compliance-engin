import re
from typing import List, Tuple, Optional, Union, Dict, Set
from app.models import RuleResult, OCRLine
from app.engine.exemption import is_nutrition_or_ingredient_line

CONFIDENCE_THRESHOLD = 0.60

# Exact statutory reason text mandated for dual pricing
DUAL_MRP_REASON = "Dual pricing detected — Rule 32(2) prohibits multiple MRP declarations without proper correction procedure."


# ==============================================================================
# OCR NORMALIZATION HELPERS (Controlled Tolerance Layer)
# ==============================================================================

def normalize_ocr_text(text: str) -> str:
    """Normalizes OCR line spacing and common whitespace noise while preserving characters."""
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


def normalize_numeric_token(token: str) -> str:
    """
    Normalizes numeric OCR artifacts within extracted price/quantity tokens ONLY.
    Replaces 'O'/'o' with '0', 'l'/'I' with '1', and cleans punctuation noise.
    Never applied globally to arbitrary prose.
    """
    if not token:
        return ""
    clean = token.strip().rstrip(".,;*#")
    # Replace uppercase/lowercase O with 0 only if adjacent to digits or forming digits
    clean = re.sub(r"(?<=\d)[oO]", "0", clean)
    clean = re.sub(r"[oO](?=\d)", "0", clean)
    # If token is something like '2O', handle it
    if re.match(r"^\d+[oO]$", clean):
        clean = clean[:-1] + "0"
    return clean


def parse_price_value(raw_val: str) -> Optional[float]:
    """Parses a normalized price string into a float."""
    normalized = normalize_numeric_token(raw_val)
    try:
        val = float(normalized)
        return round(val, 2)
    except (ValueError, TypeError):
        return None


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
    If confidence is below 0.60, mark as 'UNCERTAIN' instead of clean PASS/FLAGGED.
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


# ==============================================================================
# FIELD 1: MAXIMUM RETAIL PRICE (MRP) & DUAL PRICING DETECTION
# ==============================================================================

def check_mrp(text_or_ocr_lines: Union[List[str], List[OCRLine]]) -> RuleResult:
    """
    Field 1: Maximum Retail Price (MRP) - Rule 6(1)(e) & Rule 32(2)
    
    Robustness requirements:
    1. Matches MRP keywords: MRP, M.R.P, MRP., M.R.P., Maximum Retail Price, MaximumRetailPrice
       with optional colons, dots, spaces, and currency symbols (₹, Rs, Rs., INR).
    2. Tolerate OCR noise in price tokens (e.g. 'MRP Rs.2O' -> ₹20.0).
    3. Dual MRP Detection:
       Searches remainder of current line and next line for multiple distinct MRP declarations.
       If distinct conflicting prices are detected (e.g. MRP Rs.20 MRPRs.25*), returns FLAGGED
       with exact message: DUAL_MRP_REASON.
    4. Identical declarations (e.g. 'MRP Rs.20 MRP Rs.20') are NOT flagged as conflicting.
    """
    lines, confidences = _extract_text_and_confidences(text_or_ocr_lines)
    full_text = " ".join(lines)

    mrp_kw_pattern = r"(?:m\.?\s*r\.?\s*p\.?|max(?:imum)?\s*retail\s*price|maximumretailprice)"
    currency_pattern = r"(?:(?:rs\.?|inr|₹)\s*)"
    price_pattern = r"([0-9oO]+(?:\.[0-9oO]{1,2})?)\s*(?:\*)?"

    mrp_regex = re.compile(
        rf"{mrp_kw_pattern}\s*(?:is)?\s*[:\.\s-]*\s*(?:{currency_pattern})?{price_pattern}",
        re.IGNORECASE
    )

    detected_items = []

    for idx, line in enumerate(lines):
        if is_nutrition_or_ingredient_line(line):
            continue

        for match in mrp_regex.finditer(line):
            raw_matched_text = match.group(0).strip()
            raw_val = match.group(1)
            parsed_price = parse_price_value(raw_val)
            if parsed_price is not None:
                detected_items.append((raw_matched_text, parsed_price, idx, confidences[idx]))

    # Cross-line check: Keyword on line i, price on line i+1
    if not detected_items:
        for idx in range(len(lines) - 1):
            curr_line = lines[idx].strip()
            next_line = lines[idx + 1].strip()
            if is_nutrition_or_ingredient_line(curr_line) or is_nutrition_or_ingredient_line(next_line):
                continue

            if re.search(rf"\b{mrp_kw_pattern}[:\s-]*$", curr_line, re.IGNORECASE):
                p_match = re.search(rf"^(?:{currency_pattern})?{price_pattern}\b", next_line, re.IGNORECASE)
                if p_match:
                    combined_text = f"{curr_line} {next_line}"
                    parsed_price = parse_price_value(p_match.group(1))
                    if parsed_price is not None:
                        conf_val = min(c for c in [confidences[idx], confidences[idx+1]] if c is not None) if any(c is not None for c in [confidences[idx], confidences[idx+1]]) else None
                        detected_items.append((combined_text, parsed_price, idx, conf_val))

    if not detected_items:
        return RuleResult(
            field_id="mrp",
            field_name="Maximum Retail Price (MRP)",
            rule_reference="Rule 6(1)(e) & Rule 32, Legal Metrology (Packaged Commodities) Rules, 2011",
            status="FAIL",
            found=False,
            matched_text=None,
            confidence_score=None,
            flag=None,
            details="No valid MRP declaration or price amount detected in proximity to required MRP keywords."
        )

    prices_list = [item[1] for item in detected_items]
    distinct_prices = sorted(list(set(prices_list)))
    primary_item = detected_items[0]
    primary_text = primary_item[0]
    primary_conf = primary_item[3]

    sticker_keywords = bool(re.search(r"\b(sticker|pasted\s*price|revised\s*mrp|re-labeled|over-printed|dual\s*price)\b", full_text, re.IGNORECASE))
    has_dual_mrp = len(distinct_prices) > 1

    if has_dual_mrp or sticker_keywords:
        all_matched_texts = " | ".join(item[0] for item in detected_items)
        base_status = "FLAGGED"
        
        if has_dual_mrp:
            prices_formatted = " / ".join(f"₹{p}" for p in distinct_prices)
            flag_msg = f"{DUAL_MRP_REASON} (Detected: {prices_formatted})"
            details = f"{DUAL_MRP_REASON} Detected values: {prices_formatted}."
        else:
            flag_msg = "Price sticker / overprinting alteration keyword detected on label (Rule 32)."
            details = f"MRP declaration is present ('{primary_text}'), but price alteration or sticker was flagged."

        status, conf_score, final_details, conf_flag = _check_confidence_status(primary_conf, base_status, details)
        if conf_flag:
            flag_msg += f" | {conf_flag}"

        return RuleResult(
            field_id="mrp",
            field_name="Maximum Retail Price (MRP)",
            rule_reference="Rule 6(1)(e) & Rule 32(2), Legal Metrology (Packaged Commodities) Rules, 2011",
            status=status,
            found=True,
            matched_text=all_matched_texts,
            confidence_score=conf_score,
            flag=flag_msg,
            details=final_details
        )

    base_status = "PASS"
    default_details = f"Compliant MRP declaration detected: '{primary_text}' (₹{distinct_prices[0]})."
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


# ==============================================================================
# FIELD 2: NET QUANTITY HARDENING & SI UNIT VALIDATION
# ==============================================================================

def check_net_quantity(text_or_ocr_lines: Union[List[str], List[OCRLine]]) -> RuleResult:
    """
    Field 2: Net Quantity - Rule 6(1)(b) & Rule 12
    """
    lines, confidences = _extract_text_and_confidences(text_or_ocr_lines)

    kw_pattern = r"(?:net\s*(?:wt\.?|weight|qty\.?|quantity|vol\.?|volume|content|contents)|contains|package\s*size|pkg\s*size)"
    prefix_regex = re.compile(
        rf"(?:{kw_pattern})\s*[:\.\s-]*([0-9oO]+(?:\.[0-9oO]+)?)\s*([a-zA-Z\.]+)",
        re.IGNORECASE
    )

    std_units = {"g", "kg", "mg", "ml", "l", "L"}
    non_std_units = {"gm", "gms", "kgs", "ltr", "ltrs", "ml.", "gm.", "gms.", "gram", "grams", "kilo", "kilos"}

    for idx, line in enumerate(lines):
        if is_nutrition_or_ingredient_line(line):
            continue

        match = prefix_regex.search(line)
        if match:
            raw_val = match.group(1)
            parsed_val = normalize_numeric_token(raw_val)
            raw_unit = match.group(2).strip().rstrip('.,;')
            unit_lower = raw_unit.lower()
            full_match = match.group(0).strip()
            conf = confidences[idx]

            if raw_unit in std_units or unit_lower in {"g", "kg", "mg", "ml", "l"}:
                base_status = "PASS"
                default_details = f"Standard SI net quantity declaration detected: '{full_match}' ({parsed_val} {raw_unit})."
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
                base_status = "FLAGGED"
                default_details = f"Net quantity detected as '{full_match}', but uses non-standard unit '{raw_unit}'."
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

    # Standalone line check
    standalone_std = re.compile(r"^(?:(?:net\s*(?:wt\.?|weight|qty\.?|quantity)?[:\.\s-]*)?|\b)([0-9oO]+(?:\.[0-9oO]+)?)\s*(kg|g|mg|ml|l|L)\b", re.IGNORECASE)
    standalone_non_std = re.compile(r"^(?:(?:net\s*(?:wt\.?|weight|qty\.?|quantity)?[:\.\s-]*)?|\b)([0-9oO]+(?:\.[0-9oO]+)?)\s*(gms?|kgs|ltrs?|m\.l\.|gm\.|gms\.)\b", re.IGNORECASE)

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
            base_status = "FLAGGED"
            default_details = f"Net quantity detected as '{matched_text}' using non-standard unit notation '{unit}'."
            status, conf_score, details, conf_flag = _check_confidence_status(conf, base_status, default_details)
            flag_str = f"Non-standard unit '{unit}' used. Rule 12 prescribes standard SI symbols: 'g', 'kg', 'ml', 'l'."
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


# ==============================================================================
# FIELD 3: MANUFACTURE / PACKING DATE HARDENING
# ==============================================================================

def check_mfg_date(text_or_ocr_lines: Union[List[str], List[OCRLine]]) -> RuleResult:
    """
    Field 3: Month & Year of Manufacture / Packing - Rule 6(1)(d)
    """
    lines, confidences = _extract_text_and_confidences(text_or_ocr_lines)

    months_str = r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)"
    date_regex = rf"(?:(?:0?[1-9]|[12][0-9]|3[01])[\/\.-])?(?:(?:0?[1-9]|1[0-2])|{months_str})[\/\.\s,-]+(?:20[2-9][0-9]|[2-9][0-9])"
    mfg_kw = r"(?:mfg\s*dt\.?|mfg\.?|mfd\.?|manufactur(?:ed|ing)|pkd\.?|packed(?:\s*on)?|pack(?:ing)?|pkg|date\s*of\s*(?:mfg|mfd|pkd|packing|manufacture))"
    
    mfg_pattern = re.compile(
        rf"(?:{mfg_kw})\s*[:\.\s-]*({date_regex})",
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

        if re.search(rf"\b{mfg_kw}\b", line, re.IGNORECASE):
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

    for idx in range(len(lines) - 1):
        curr_line = lines[idx].strip()
        next_line = lines[idx + 1].strip()
        if is_nutrition_or_ingredient_line(curr_line) or is_nutrition_or_ingredient_line(next_line):
            continue
        if re.search(rf"\b{mfg_kw}[:\s-]*$", curr_line, re.IGNORECASE):
            d_match = re.search(rf"^{date_regex}\b", next_line, re.IGNORECASE)
            if d_match:
                combined = f"{curr_line} {next_line}"
                conf_val = min(c for c in [confidences[idx], confidences[idx+1]] if c is not None) if any(c is not None for c in [confidences[idx], confidences[idx+1]]) else None
                base_status = "PASS"
                default_details = f"Manufacture/Packing date declaration detected: '{combined}'."
                status, conf_score, details, conf_flag = _check_confidence_status(conf_val, base_status, default_details)
                return RuleResult(
                    field_id="mfg_date",
                    field_name="Month & Year of Manufacture / Packing",
                    rule_reference="Rule 6(1)(d), Legal Metrology (Packaged Commodities) Rules, 2011",
                    status=status,
                    found=True,
                    matched_text=combined,
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


# ==============================================================================
# FIELD 4: MANUFACTURER / PACKER NAME & ADDRESS HARDENING
# ==============================================================================

def check_manufacturer_address(text_or_ocr_lines: Union[List[str], List[OCRLine]]) -> RuleResult:
    """
    Field 4: Manufacturer / Packer / Importer Name & Address - Rule 6(1)(a)
    """
    lines, confidences = _extract_text_and_confidences(text_or_ocr_lines)

    mfr_kw = r"(?:mfd\.?\s*by|mfdby|manufactured\s*(?:&|and)?\s*packed\s*by|manufactured\s*by|manufacturedby|marketed\s*by|marketedby|mktd\.?\s*by|packed\s*by|packedby|pkd\.?\s*by|imported\s*by|importedby|distributed\s*by|distributedby)"
    addr_pattern = re.compile(
        rf"(?:{mfr_kw})\s*[:\.\s-]*([^\n\r;]{{4,150}})",
        re.IGNORECASE
    )

    def is_meaningful_address_text(val: str) -> bool:
        if not val or len(val.strip()) < 4:
            return False
        clean = val.strip()
        alpha_count = len(re.findall(r"[a-zA-Z]", clean))
        if alpha_count < 3:
            return False
        if re.match(r"^[\W_0-9]+$", clean):
            return False
        return True

    for idx, line in enumerate(lines):
        if is_nutrition_or_ingredient_line(line):
            continue

        match = addr_pattern.search(line)
        if match:
            extracted_addr = match.group(1).strip()
            if is_meaningful_address_text(extracted_addr):
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

    for idx in range(len(lines) - 1):
        curr_line = lines[idx].strip()
        next_line = lines[idx + 1].strip()
        if is_nutrition_or_ingredient_line(curr_line) or is_nutrition_or_ingredient_line(next_line):
            continue

        if re.search(rf"\b{mfr_kw}[:\s-]*$", curr_line, re.IGNORECASE):
            if is_meaningful_address_text(next_line):
                combined = f"{curr_line} {next_line}"
                conf_val = min(c for c in [confidences[idx], confidences[idx+1]] if c is not None) if any(c is not None for c in [confidences[idx], confidences[idx+1]]) else None
                base_status = "PASS"
                default_details = f"Manufacturer/Packer declaration detected: '{combined}'."
                status, conf_score, details, conf_flag = _check_confidence_status(conf_val, base_status, default_details)
                return RuleResult(
                    field_id="address",
                    field_name="Name & Address of Manufacturer / Packer / Importer",
                    rule_reference="Rule 6(1)(a), Legal Metrology (Packaged Commodities) Rules, 2011",
                    status=status,
                    found=True,
                    matched_text=combined,
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


# ==============================================================================
# FIELD 5: CONSUMER CARE DETAILS HARDENING
# ==============================================================================

def check_consumer_care(text_or_ocr_lines: Union[List[str], List[OCRLine]]) -> RuleResult:
    """
    Field 5: Consumer Care Details - Rule 6(1)(f)
    
    Robustness requirements:
    1. Indian 10-digit mobile numbers with varied spacing/prefixes:
       9876543210, 98765 43210, 9876-543-210, 98765-43210, +91 9876543210, +91-9876543210, 91 9876543210.
    2. Toll-free numbers: 1800 123 4567, 1800-123-4567, 18001234567, 1800-200-4567.
    3. Valid email pattern: consumer@example.com, care.support@example.in, help@company.co.in.
    4. Rejects lines containing only care keywords without actual phone/email (e.g. 'MISSING CONSUMER CARE').
    """
    lines, confidences = _extract_text_and_confidences(text_or_ocr_lines)

    email_pattern = re.compile(r"\b[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+\b")
    
    phone_pattern = re.compile(
        r"(?:1800[\s-]?\d{3}[\s-]?\d{3,4}\b|(?:\+91[\s-]*)?[6-9]\d{4}[\s-]?\d{5}\b|(?:\+91[\s-]*)?[6-9]\d{3}[\s-]?\d{3}[\s-]?\d{3}\b|0\d{2,4}[\s-]\d{6,8}\b)",
        re.IGNORECASE
    )

    for idx, line in enumerate(lines):
        clean_line = line.strip()
        conf = confidences[idx]

        # Ignore obvious negative keywords or headers like "MISSING CONSUMER CARE"
        if re.search(r"\b(?:missing|absent|none|no\s*consumer\s*care)\b", clean_line, re.IGNORECASE):
            continue

        # 1. Match Email
        email_match = email_pattern.search(clean_line)
        if email_match:
            matched_email = email_match.group(0)
            base_status = "PASS"
            default_details = f"Consumer grievance email contact detected: '{matched_email}'."
            status, conf_score, details, conf_flag = _check_confidence_status(conf, base_status, default_details)
            return RuleResult(
                field_id="consumer_care",
                field_name="Consumer Care Details",
                rule_reference="Rule 6(1)(f), Legal Metrology (Packaged Commodities) Rules, 2011",
                status=status,
                found=True,
                matched_text=clean_line,
                confidence_score=conf_score,
                flag=conf_flag,
                details=details
            )

        # 2. Match Phone / Toll-free
        phone_match = phone_pattern.search(clean_line)
        if phone_match:
            matched_phone = phone_match.group(0)
            base_status = "PASS"
            default_details = f"Consumer grievance telephone/helpline detected: '{matched_phone}'."
            status, conf_score, details, conf_flag = _check_confidence_status(conf, base_status, default_details)
            return RuleResult(
                field_id="consumer_care",
                field_name="Consumer Care Details",
                rule_reference="Rule 6(1)(f), Legal Metrology (Packaged Commodities) Rules, 2011",
                status=status,
                found=True,
                matched_text=clean_line,
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
        details="No consumer grievance phone number, helpline, or email address declaration found."
    )


# ==============================================================================
# FIELD 6: GENERIC NAME
# ==============================================================================

def check_generic_name(text_or_ocr_lines: Union[List[str], List[OCRLine]]) -> RuleResult:
    lines, confidences = _extract_text_and_confidences(text_or_ocr_lines)
    kw_pattern = r"(?:generic\s*name|common\s*name|commodity|product(?:\s*name)?)"
    regex = re.compile(rf"(?:{kw_pattern})\s*[:\.\s-]*([a-zA-Z\s]{{3,50}})", re.IGNORECASE)
    
    for idx, line in enumerate(lines):
        if is_nutrition_or_ingredient_line(line): continue
        match = regex.search(line)
        if match:
            matched_text = match.group(0).strip()
            conf = confidences[idx]
            status, conf_score, details, conf_flag = _check_confidence_status(conf, "PASS", f"Generic name detected: '{matched_text}'.")
            return RuleResult(
                field_id="generic_name",
                field_name="Generic / Common Name",
                rule_reference="Rule 6(1)(b), Legal Metrology Rules",
                status=status, found=True, matched_text=matched_text,
                confidence_score=conf_score, flag=conf_flag, details=details
            )
            
    return RuleResult(
        field_id="generic_name", field_name="Generic / Common Name",
        rule_reference="Rule 6(1)(b), Legal Metrology Rules",
        status="FAIL", found=False, matched_text=None, confidence_score=None, flag=None,
        details="No generic name or product commodity declaration found."
    )

# ==============================================================================
# FIELD 7: COUNTRY OF ORIGIN
# ==============================================================================

def check_country_of_origin(text_or_ocr_lines: Union[List[str], List[OCRLine]]) -> RuleResult:
    lines, confidences = _extract_text_and_confidences(text_or_ocr_lines)
    kw_pattern = r"(?:country\s*of\s*origin|made\s*in|product\s*of|manufactured\s*in|produce\s*of)"
    regex = re.compile(rf"(?:{kw_pattern})\s*[:\.\s-]*([a-zA-Z\s]{{3,30}})", re.IGNORECASE)
    
    is_imported = False
    full_text = " ".join(lines).lower()
    if re.search(r"\b(imported\s*by|importer|import|imported)\b", full_text):
        is_imported = True

    for idx, line in enumerate(lines):
        if is_nutrition_or_ingredient_line(line): continue
        match = regex.search(line)
        if match:
            matched_text = match.group(0).strip()
            conf = confidences[idx]
            status, conf_score, details, conf_flag = _check_confidence_status(conf, "PASS", f"Country of origin detected: '{matched_text}'.")
            return RuleResult(
                field_id="country_of_origin",
                field_name="Country of Origin",
                rule_reference="Rule 6(1)(a), Legal Metrology Rules",
                status=status, found=True, matched_text=matched_text,
                confidence_score=conf_score, flag=conf_flag, details=details
            )
            
    if is_imported:
        return RuleResult(
            field_id="country_of_origin", field_name="Country of Origin",
            rule_reference="Rule 6(1)(a), Legal Metrology Rules",
            status="FAIL", found=False, matched_text=None, confidence_score=None, flag=None,
            details="Product appears to be imported, but no country of origin declaration was found."
        )
    else:
        return RuleResult(
            field_id="country_of_origin", field_name="Country of Origin",
            rule_reference="Rule 6(1)(a), Legal Metrology Rules",
            status="PASS", found=False, matched_text=None, confidence_score=None, flag=None,
            details="Product does not appear to be imported. Country of Origin check waived."
        )

# ==============================================================================
# FIELD 8: UNIT SALE PRICE
# ==============================================================================

def check_unit_sale_price(text_or_ocr_lines: Union[List[str], List[OCRLine]]) -> RuleResult:
    lines, confidences = _extract_text_and_confidences(text_or_ocr_lines)
    kw_pattern = r"(?:usp|unit\s*sale\s*price|price\s*per|unit\s*price)"
    currency_pattern = r"(?:rs\.?|inr|₹)"
    unit_pattern = r"(?:per|/)\s*(?:g|gm|gms|kg|kgs|ml|l|L|piece|item|unit)\b"
    
    regex = re.compile(
        rf"(?:{kw_pattern})\s*[:\.\s-]*\s*(?:{currency_pattern}\s*)?([0-9oO]+(?:\.[0-9oO]+)?)\s*(?:{currency_pattern}\s*)?{unit_pattern}",
        re.IGNORECASE
    )
    
    for idx, line in enumerate(lines):
        if is_nutrition_or_ingredient_line(line): continue
        match = regex.search(line)
        if match:
            matched_text = match.group(0).strip()
            conf = confidences[idx]
            status, conf_score, details, conf_flag = _check_confidence_status(conf, "PASS", f"Unit sale price detected: '{matched_text}'.")
            return RuleResult(
                field_id="unit_sale_price",
                field_name="Unit Sale Price",
                rule_reference="Rule 6(1)(e), Legal Metrology Rules",
                status=status, found=True, matched_text=matched_text,
                confidence_score=conf_score, flag=conf_flag, details=details
            )
            
    return RuleResult(
        field_id="unit_sale_price", field_name="Unit Sale Price",
        rule_reference="Rule 6(1)(e), Legal Metrology Rules",
        status="FAIL", found=False, matched_text=None, confidence_score=None, flag=None,
        details="No Unit Sale Price (USP) declaration found."
    )


# ==============================================================================
# FIELD 9: BEST BEFORE / USE BY
# ==============================================================================

def check_best_before(text_or_ocr_lines: Union[List[str], List[OCRLine]]) -> RuleResult:
    lines, confidences = _extract_text_and_confidences(text_or_ocr_lines)
    kw_pattern = r"(?:best\s*before|use\s*by|expiry(?: date)?|exp\s*date|exp\.?)"
    date_regex = r"([0-9\/\.\s-]+(?:months|days|years)?(?:from.*)?|[0-9\/\.-]+)"
    regex = re.compile(rf"(?:{kw_pattern})\s*[:\.\s-]*{date_regex}", re.IGNORECASE)
    
    for idx, line in enumerate(lines):
        if is_nutrition_or_ingredient_line(line): continue
        match = regex.search(line)
        if match:
            matched_text = match.group(0).strip()
            conf = confidences[idx]
            status, conf_score, details, conf_flag = _check_confidence_status(conf, "PASS", f"Best Before / Use By detected: '{matched_text}'.")
            return RuleResult(
                field_id="best_before",
                field_name="Best Before / Use By Date",
                rule_reference="Rule 6(1)(d), Legal Metrology Rules",
                status=status, found=True, matched_text=matched_text,
                confidence_score=conf_score, flag=conf_flag, details=details
            )
            
    return RuleResult(
        field_id="best_before", field_name="Best Before / Use By Date",
        rule_reference="Rule 6(1)(d), Legal Metrology Rules",
        status="FAIL", found=False, matched_text=None, confidence_score=None, flag=None,
        details="No Best Before or Expiry date declaration found."
    )


# ==============================================================================
# FIELD 10: FONT LEGIBILITY THRESHOLD
# ==============================================================================

def check_font_legibility(text_or_ocr_lines: Union[List[str], List[OCRLine]]) -> RuleResult:
    """
    Evaluates pixel height of bounding boxes to warn if text is suspiciously small (micro-print).
    Assumes standard OCR line bbox format.
    """
    MIN_PIXEL_HEIGHT = 15
    smallest_height = float('inf')
    suspicious_lines = []
    has_bboxes = False
    
    for item in text_or_ocr_lines:
        if isinstance(item, OCRLine) and item.bbox and len(item.bbox) >= 4:
            has_bboxes = True
            try:
                y_coords = [pt[1] for pt in item.bbox]
                height = max(y_coords) - min(y_coords)
                if height < smallest_height:
                    smallest_height = height
                if height < MIN_PIXEL_HEIGHT:
                    suspicious_lines.append(item.text)
            except Exception:
                continue

    if not has_bboxes:
        return RuleResult(
            field_id="font_legibility",
            field_name="Font Height & Legibility",
            rule_reference="Rule 7, Legal Metrology Rules",
            status="UNCERTAIN", found=False, matched_text=None, confidence_score=None, flag=None,
            details="No spatial bounding boxes provided; cannot evaluate font height."
        )

    if suspicious_lines:
        return RuleResult(
            field_id="font_legibility",
            field_name="Font Height & Legibility",
            rule_reference="Rule 7, Legal Metrology Rules",
            status="WARNING", found=True, matched_text=" | ".join(suspicious_lines[:3]), confidence_score=None,
            flag=f"Micro-print detected (<{MIN_PIXEL_HEIGHT}px height).",
            details=f"Warning: {len(suspicious_lines)} text lines detected with font height under {MIN_PIXEL_HEIGHT}px. Ensure declarations meet statutory 1mm/2.5mm minimum height based on display panel area."
        )

    return RuleResult(
        field_id="font_legibility",
        field_name="Font Height & Legibility",
        rule_reference="Rule 7, Legal Metrology Rules",
        status="PASS", found=True, matched_text=None, confidence_score=None, flag=None,
        details=f"All detected text lines appear sufficiently sized (smallest height: {int(smallest_height)}px)."
    )


# ==============================================================================
# EVALUATE ALL RULES
# ==============================================================================

def evaluate_all_rules(text_or_ocr_lines: Union[List[str], List[OCRLine]], extended: bool = False) -> List[RuleResult]:
    """
    Evaluates mandatory Legal Metrology declarations under Rule 6.
    By default returns the 5 statutory mandatory declaration fields:
    1. Maximum Retail Price (MRP) - Rule 6(1)(e)
    2. Net Quantity - Rule 6(1)(b)
    3. Month & Year of Manufacture / Packing - Rule 6(1)(d)
    4. Name & Address of Manufacturer / Packer / Importer - Rule 6(1)(a)
    5. Consumer Care Details - Rule 6(1)(f)

    If extended=True, includes supplementary advisory declarations.
    """
    rules = [
        check_mrp(text_or_ocr_lines),
        check_net_quantity(text_or_ocr_lines),
        check_mfg_date(text_or_ocr_lines),
        check_manufacturer_address(text_or_ocr_lines),
        check_consumer_care(text_or_ocr_lines)
    ]
    if extended:
        rules.extend([
            check_generic_name(text_or_ocr_lines),
            check_country_of_origin(text_or_ocr_lines),
            check_unit_sale_price(text_or_ocr_lines),
            check_best_before(text_or_ocr_lines),
            check_font_legibility(text_or_ocr_lines)
        ])
    return rules

