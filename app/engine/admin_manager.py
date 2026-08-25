import os
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from app.db.supabase_client import get_recent_scans

logger = logging.getLogger("compliance_engine.admin")

RULES_FILE = os.path.join(os.path.dirname(__file__), "..", "..", "data", "statutory_rules.json")

ADMIN_USERS = [
    {
        "email": "admin@metrasetu.gov.in",
        "password": "MetraAdmin@2026",
        "name": "Senior Metrology Officer",
        "role": "State Enforcement Controller",
        "badge_id": "LM-DEL-0428"
    },
    {
        "email": "inspector@metrasetu.gov.in",
        "password": "admin123",
        "name": "Field Metrology Inspector",
        "role": "Compliance Screening Officer",
        "badge_id": "LM-FLD-0199"
    }
]

def verify_admin_login(email: str, password: str) -> Optional[Dict[str, Any]]:
    """Verifies admin credentials and returns user profile if valid."""
    cleaned_email = (email or "").strip().lower()
    for user in ADMIN_USERS:
        if user["email"].lower() == cleaned_email and user["password"] == password:
            token = f"token_{int(datetime.now().timestamp())}_{user['badge_id']}"
            return {
                "token": token,
                "email": user["email"],
                "name": user["name"],
                "role": user["role"],
                "badge_id": user["badge_id"]
            }
    return None

def _load_data() -> Dict[str, Any]:
    try:
        if os.path.exists(RULES_FILE):
            with open(RULES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading statutory rules from {RULES_FILE}: {e}")
    return {"rules": [], "amendments": [], "violation_actions": {}}


def _save_data(data: Dict[str, Any]) -> bool:
    try:
        os.makedirs(os.path.dirname(RULES_FILE), exist_ok=True)
        with open(RULES_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        logger.error(f"Error saving statutory rules to {RULES_FILE}: {e}")
        return False


def get_all_rules() -> List[Dict[str, Any]]:
    """Returns list of all configured Legal Metrology statutory rules."""
    data = _load_data()
    return data.get("rules", [])


def update_rule(rule_id: str, update_fields: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Updates statutory parameters or descriptions for an existing rule."""
    data = _load_data()
    rules = data.get("rules", [])
    for rule in rules:
        if rule.get("id") == rule_id or rule.get("rule_code") == rule_id:
            for k, v in update_fields.items():
                if k != "id":
                    rule[k] = v
            rule["last_updated"] = datetime.now().strftime("%Y-%m-%d")
            _save_data(data)
            return rule
    return None


def add_rule(new_rule: Dict[str, Any]) -> Dict[str, Any]:
    """Adds a new statutory rule or regulatory standard."""
    data = _load_data()
    rules = data.get("rules", [])
    if "id" not in new_rule or not new_rule["id"]:
        new_rule["id"] = f"rule_{int(datetime.now().timestamp())}"
    new_rule["last_updated"] = datetime.now().strftime("%Y-%m-%d")
    rules.append(new_rule)
    data["rules"] = rules
    _save_data(data)
    return new_rule


def get_all_amendments() -> List[Dict[str, Any]]:
    """Returns gazette amendments and regulatory circulars."""
    data = _load_data()
    return data.get("amendments", [])


def add_amendment(new_amd: Dict[str, Any]) -> Dict[str, Any]:
    """Publishes a new gazette notification / amendment circular."""
    data = _load_data()
    amendments = data.get("amendments", [])
    if "id" not in new_amd or not new_amd["id"]:
        new_amd["id"] = f"amd_{int(datetime.now().timestamp())}"
    amendments.insert(0, new_amd)
    data["amendments"] = amendments
    _save_data(data)
    return new_amd


def get_raised_violations(limit: int = 100) -> List[Dict[str, Any]]:
    """
    Extracts all raised statutory violations from inspection screening scans.
    Enriches with action workflow status, statutory penalty details, and officer notes.
    """
    data = _load_data()
    violation_actions = data.get("violation_actions", {})
    recent_scans = get_recent_scans(limit=limit)

    violations = []
    for scan in recent_scans:
        overall_status = (scan.get("overall_status") or "").upper()
        if overall_status in ["NON_COMPLIANT", "FLAGGED", "UNCERTAIN"]:
            scan_id = scan.get("scan_id", "UNKNOWN")
            fields = scan.get("fields", [])
            failed_fields = [f for f in fields if f.get("status") in ["FAIL", "FLAGGED", "WARNING", "UNCERTAIN"]]

            # Determine primary violation description & governing section
            violation_types = []
            statutory_reasons = []
            has_dual_mrp = False
            has_non_std_unit = False

            for f in failed_fields:
                fname = f.get("field_name") or f.get("field_id", "Field")
                flag_text = f.get("flag") or f.get("details") or ""
                if "Dual pricing" in flag_text or "Rule 32" in flag_text:
                    has_dual_mrp = True
                    violation_types.append("Dual MRP Alteration (Rule 32)")
                    statutory_reasons.append("Prohibited multiple MRP declaration on package")
                elif "Non-standard unit" in flag_text or "standard SI" in flag_text:
                    has_non_std_unit = True
                    violation_types.append("Non-Standard Metric Unit (Rule 12)")
                    statutory_reasons.append("Deprecated unit used instead of standard SI symbols")
                else:
                    violation_types.append(f"Missing {fname} (Rule 6)")
                    statutory_reasons.append(flag_text[:80])

            # Severity
            if has_dual_mrp:
                severity = "CRITICAL"
                section_code = "Section 36(1) / Section 39"
            elif has_non_std_unit:
                severity = "HIGH"
                section_code = "Section 36(2)"
            elif overall_status == "NON_COMPLIANT":
                severity = "HIGH"
                section_code = "Section 36(1)"
            else:
                severity = "MEDIUM"
                section_code = "Rule 7 / Rule 6"

            action_data = violation_actions.get(scan_id, {
                "status": "PENDING_REVIEW",
                "officer_notes": "Automated AI screening flag raised.",
                "assigned_officer": "Legal Metrology Enforcement Officer",
                "last_action_date": scan.get("timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            })

            violations.append({
                "scan_id": scan_id,
                "timestamp": scan.get("timestamp"),
                "filename": scan.get("filename", "label_inspection.png"),
                "overall_status": overall_status,
                "severity": severity,
                "section_code": section_code,
                "violation_types": violation_types,
                "failed_declarations_count": len(failed_fields),
                "failed_fields": failed_fields,
                "action_status": action_data.get("status", "PENDING_REVIEW"),
                "officer_notes": action_data.get("officer_notes", ""),
                "assigned_officer": action_data.get("assigned_officer", "Legal Metrology Officer"),
                "last_action_date": action_data.get("last_action_date", scan.get("timestamp"))
            })

    return violations


def update_violation_status(scan_id: str, new_status: str, officer_notes: Optional[str] = None, officer_name: Optional[str] = None) -> Dict[str, Any]:
    """Updates the action status (e.g. DRAFT_NOTICE, ESCALATED, RESOLVED) for a raised violation."""
    data = _load_data()
    violation_actions = data.get("violation_actions", {})
    current = violation_actions.get(scan_id, {})
    current["status"] = new_status
    if officer_notes is not None:
        current["officer_notes"] = officer_notes
    if officer_name is not None:
        current["assigned_officer"] = officer_name
    current["last_action_date"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    violation_actions[scan_id] = current
    data["violation_actions"] = violation_actions
    _save_data(data)
    return current
