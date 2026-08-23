import re
from typing import List, Union, Optional
from app.models import ExemptionResult, OCRLine

# Nutrition information / ingredient keywords that must NOT trigger quantity exemptions
NUTRITION_OR_INGREDIENT_KEYWORDS = [
    r"\bprotein\b",
    r"\bcarbohydrate[s]?\b",
    r"\btotal\s+fat\b",
    r"\bsaturated\s+fat\b",
    r"\btrans\s+fat\b",
    r"\bcholesterol\b",
    r"\bsodium\b",
    r"\bdietary\s+fib[er|re]\b",
    r"\bsugar[s]?\b",
    r"\badded\s+sugar[s]?\b",
    r"\benergy\b",
    r"\bkcal\b",
    r"\bcalories\b",
    r"\bserving\s+size\b",
    r"\bservings\s+per\b",
    r"\bper\s+100\s*g\b",
    r"\bper\s+100\s*ml\b",
    r"\bper\s+serve\b",
    r"\bnutrition(?:al)?\s+(?:facts|info|information)\b",
    r"\bingredients?[:\s]",
]

def is_nutrition_or_ingredient_line(line: str) -> bool:
    """Returns True if the line contains nutritional facts, ingredients list, or nutrient breakdowns."""
    lower = line.lower()
    for kw in NUTRITION_OR_INGREDIENT_KEYWORDS:
        if re.search(kw, lower):
            return True
    return False


def check_exemptions(text_or_ocr_lines: Union[List[str], List[OCRLine]]) -> ExemptionResult:
    """
    Checks extracted text against Legal Metrology exemption conditions under Rule 3 and Rule 26.
    If ANY condition matches, returns is_exempt=True with details.

    Rules strictly enforced:
    - Small package (<=10g / <=10ml) check ONLY matches when explicitly adjacent to net-quantity keywords:
      ('net wt', 'net weight', 'net qty', 'net quantity', 'contains', 'net content', 'net contents', 'net vol', 'net volume').
    - Bare numbers or numbers in nutrition/ingredient panels NEVER trigger exemptions.
    """
    # Normalize lines into strings
    lines: List[str] = []
    for item in text_or_ocr_lines:
        if isinstance(item, OCRLine):
            lines.append(item.text)
        elif isinstance(item, str):
            lines.append(item)
        else:
            lines.append(str(item))

    full_text = " ".join(lines)
    lower_text = full_text.lower()

    # 1. Condition: "not for retail sale" / Institutional supply
    not_for_retail_patterns = [
        r"\bnot\s+for\s+retail\s+sale\b",
        r"\bnot\s+for\s+retail\b",
        r"\bfor\s+institutional\s+consumers?\b",
        r"\bfor\s+industrial\s+consumers?\b",
        r"\bnot\s+for\s+individual\s+resale\b",
        r"\bfor\s+hotel\s+hospital\s+institutional\b",
    ]
    for pattern in not_for_retail_patterns:
        match = re.search(pattern, lower_text)
        if match:
            return ExemptionResult(
                is_exempt=True,
                matched_condition="Not for retail sale / Institutional supply",
                reason=f"Matched non-retail clause: '{match.group(0)}'. Exempt under Rule 3 of Legal Metrology (Packaged Commodities) Rules, 2011.",
                rule_reference="Rule 3, Legal Metrology (Packaged Commodities) Rules, 2011"
            )

    # 4. Condition: Loose / Openly-sold goods
    loose_goods_patterns = [
        r"\bsold\s+by\s+weight\s+at\s+counter\b",
        r"\bsold\s+loose\b",
        r"\bloose\s+commodity\b",
        r"\bloose\s+goods\b",
        r"\bopenly\s+sold\b",
        r"\bweight\s+taken\s+at\s+counter\b",
    ]
    for pattern in loose_goods_patterns:
        match = re.search(pattern, lower_text)
        if match:
            return ExemptionResult(
                is_exempt=True,
                matched_condition="Loose / Openly-sold commodity",
                reason=f"Matched loose goods statement: '{match.group(0)}'. Commodities sold loose or weighed at counter are exempt from packaging declaration rules.",
                rule_reference="Rule 3 & Section 2(l), Legal Metrology Act, 2009"
            )

    # 2. Condition: Weight > 25kg or volume > 25 litres (except cement/fertilizer exempt up to 50kg)
    is_cement_or_fertilizer = bool(re.search(r"\b(cement|fertili[zs]er|urea|npk|potash|dap)\b", lower_text))
    max_threshold_kg = 50.0 if is_cement_or_fertilizer else 25.0

    # Filter out nutrition / ingredient lines to prevent false positive weight extractions
    filtered_lines = [l for l in lines if not is_nutrition_or_ingredient_line(l)]

    # Check for large weights/volumes (>25kg or >50kg) in non-nutrition lines with keyword proximity
    large_qty_pattern = re.compile(
        r"(?:(?:net\s*(?:wt|weight|qty|quantity|vol|volume|content|contents)?|contains|weight|gross\s*wt|pkg\s*size)[:\.\s-]+|\b)(\d+(?:\.\d+)?)\s*(kg|kgs|kilogram|kilograms|kilo|kilos|l|ltr|ltrs|liter|liters|litre|litres)\b",
        re.IGNORECASE
    )

    for line in filtered_lines:
        for m in large_qty_pattern.finditer(line):
            try:
                val = float(m.group(1))
                unit = m.group(2)
                if val > max_threshold_kg:
                    item_type = "Cement/Fertiliser" if is_cement_or_fertilizer else "Standard packaged commodity"
                    return ExemptionResult(
                        is_exempt=True,
                        matched_condition=f"Package exceeds maximum weight/volume threshold ({val} {unit})",
                        reason=f"{item_type} package declared at {val} {unit}, exceeding statutory threshold of {max_threshold_kg} kg/L under Rule 3.",
                        rule_reference="Rule 3 & Rule 26, Legal Metrology (Packaged Commodities) Rules, 2011"
                    )
            except (ValueError, IndexError):
                pass

    # 3. Condition: Net quantity <= 10g or <= 10ml (EXCEPT if text mentions "tobacco")
    is_tobacco = bool(re.search(r"\b(tobacco|gutkha|gutka|khaini|pan\s*masala|bidi|beedi|cigarette|cigar|snuff|zarda)\b", lower_text))

    if not is_tobacco:
        # STRICT KEYWORD PROXIMITY REQUIREMENT:
        # Must only match a number that appears within close proximity (same line or immediately following)
        # to one of these keywords: "net wt", "net weight", "net qty", "net quantity", "contains", "net content", "net contents", "net vol", "net volume".
        # Bare numbers or numbers inside nutrition/ingredient panels must NOT trigger the exemption.
        
        small_qty_keyword_regex = re.compile(
            r"\b(?:net\s*(?:wt|weight|qty|quantity|vol|volume|content|contents)|contains)[:\.\s-]*\s*(\d+(?:\.\d+)?)\s*(g|gm|gms|gram|grams|ml|m\.l\.|milliliter|millilitre)\b",
            re.IGNORECASE
        )

        for line in filtered_lines:
            match = small_qty_keyword_regex.search(line)
            if match:
                try:
                    val = float(match.group(1))
                    unit = match.group(2)
                    if 0 < val <= 10.0:
                        matched_phrase = match.group(0)
                        return ExemptionResult(
                            is_exempt=True,
                            matched_condition=f"Small package exemption (≤10g / ≤10ml): {matched_phrase}",
                            reason=f"Detected net quantity declaration '{matched_phrase}' (≤10g or ≤10ml). Non-tobacco packages ≤10g or ≤10ml are exempt from mandatory declarations under Rule 26.",
                            rule_reference="Rule 26, Legal Metrology (Packaged Commodities) Rules, 2011"
                        )
                except (ValueError, IndexError):
                    pass

        # Also check two consecutive lines where keyword is on line i and quantity is on line i+1
        for i in range(len(filtered_lines) - 1):
            curr_line = filtered_lines[i].strip()
            next_line = filtered_lines[i+1].strip()
            if re.search(r"\b(?:net\s*(?:wt|weight|qty|quantity|vol|volume|content|contents)|contains)[:\s-]*$", curr_line, re.IGNORECASE):
                next_match = re.search(r"^(\d+(?:\.\d+)?)\s*(g|gm|gms|gram|grams|ml|m\.l\.|milliliter|millilitre)\b", next_line, re.IGNORECASE)
                if next_match:
                    try:
                        val = float(next_match.group(1))
                        unit = next_match.group(2)
                        if 0 < val <= 10.0:
                            matched_phrase = f"{curr_line} {next_line}"
                            return ExemptionResult(
                                is_exempt=True,
                                matched_condition=f"Small package exemption (≤10g / ≤10ml): {matched_phrase}",
                                reason=f"Detected net quantity declaration '{matched_phrase}' (≤10g or ≤10ml). Non-tobacco packages ≤10g or ≤10ml are exempt under Rule 26.",
                                rule_reference="Rule 26, Legal Metrology (Packaged Commodities) Rules, 2011"
                            )
                    except (ValueError, IndexError):
                        pass

    return ExemptionResult(is_exempt=False)
