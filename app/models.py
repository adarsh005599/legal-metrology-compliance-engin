from typing import List, Optional, Any
from pydantic import BaseModel, Field

MANDATORY_DISCLAIMER = "This is a compliance-assist screening report, not a statutory notice under the Legal Metrology Act, 2009."

class OCRLine(BaseModel):
    text: str
    confidence: float
    bbox: Optional[List[Any]] = None

class LayoutRegion(BaseModel):
    region_type: str
    bbox: Optional[List[Any]] = Field(default_factory=list)
    text: Optional[str] = None

class RuleResult(BaseModel):
    field_id: str
    field_name: str
    rule_reference: str
    status: str = Field(description="PASS, FAIL, WARNING, FLAGGED, or UNCERTAIN")
    found: bool
    matched_text: Optional[str] = None
    confidence_score: Optional[float] = None
    flag: Optional[str] = None
    details: str

class ExemptionResult(BaseModel):
    is_exempt: bool
    matched_condition: Optional[str] = None
    reason: Optional[str] = None
    rule_reference: Optional[str] = "Rule 3 & Rule 26, Legal Metrology (Packaged Commodities) Rules, 2011"

class ComplianceReport(BaseModel):
    scan_id: str
    timestamp: str
    filename: Optional[str] = None
    is_exempt: bool
    exemption_details: Optional[ExemptionResult] = None
    overall_status: str = Field(description="COMPLIANT, NON_COMPLIANT, EXEMPT, or UNCERTAIN")
    fields: List[RuleResult] = []
    extracted_lines: List[OCRLine] = []
    layout_regions: List[LayoutRegion] = []
    raw_text: str = ""
    disclaimer: str = MANDATORY_DISCLAIMER
