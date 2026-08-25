"""
Root alias for app.engine.rules for legacy script imports.
"""
from app.engine.rules import (
    check_mrp,
    check_net_quantity,
    check_mfg_date,
    check_manufacturer_address,
    check_consumer_care,
    check_generic_name,
    check_country_of_origin,
    check_unit_sale_price,
    check_best_before,
    check_font_legibility,
    evaluate_all_rules,
    normalize_ocr_text,
    normalize_numeric_token,
    parse_price_value,
    DUAL_MRP_REASON
)

__all__ = [
    "check_mrp",
    "check_net_quantity",
    "check_mfg_date",
    "check_manufacturer_address",
    "check_consumer_care",
    "check_generic_name",
    "check_country_of_origin",
    "check_unit_sale_price",
    "check_best_before",
    "check_font_legibility",
    "evaluate_all_rules",
    "normalize_ocr_text",
    "normalize_numeric_token",
    "parse_price_value",
    "DUAL_MRP_REASON"
]

