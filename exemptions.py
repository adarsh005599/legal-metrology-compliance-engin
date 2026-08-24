"""
Root alias for app.engine.exemption for legacy script imports.
"""
from app.engine.exemption import (
    check_exemptions,
    is_nutrition_or_ingredient_line
)

__all__ = [
    "check_exemptions",
    "is_nutrition_or_ingredient_line"
]
