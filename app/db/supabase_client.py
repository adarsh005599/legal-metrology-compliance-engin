import os
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

from app.models import ComplianceReport

# Load environment variables from .env if present
load_dotenv()

logger = logging.getLogger("legal_metrology.supabase")
logger.setLevel(logging.INFO)

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")

_supabase_client = None
_client_initialized = False

# In-memory fallback buffer (stores up to 100 recent scans for local dev / unconfigured DB)
_memory_scans: List[Dict[str, Any]] = []


def get_supabase_client():
    """
    Initializes and returns the Supabase client if credentials are configured.
    Returns None if SUPABASE_URL or SUPABASE_KEY is missing or invalid.
    """
    global _supabase_client, _client_initialized
    if _client_initialized:
        return _supabase_client

    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.info("[DB] Supabase credentials not found in environment (SUPABASE_URL / SUPABASE_KEY). Using in-memory store.")
        _client_initialized = True
        _supabase_client = None
        return None

    try:
        from supabase import create_client, Client
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        _client_initialized = True
        logger.info(f"[DB] Supabase client successfully initialized with endpoint: {SUPABASE_URL}")
        return _supabase_client
    except Exception as e:
        logger.warning(f"[DB] Failed to initialize Supabase client: {e}. Falling back to in-memory store.")
        _client_initialized = True
        _supabase_client = None
        return None


def save_scan_record(report: ComplianceReport) -> bool:
    """
    Inserts a completed scan report record into the Supabase 'scans' table.
    Gracefully handles failures and never interrupts or blocks the scanning flow.
    """
    try:
        # Calculate summary counts
        if report.is_exempt:
            status_val = "exempt"
            fields_passed = 0
            fields_total = 0
        else:
            fields_total = len(report.fields)
            fields_passed = sum(1 for f in report.fields if f.status == "PASS")
            
            if report.overall_status == "COMPLIANT":
                status_val = "compliant"
            elif report.overall_status == "UNCERTAIN":
                status_val = "uncertain"
            else:
                status_val = "non-compliant"

        # Prepare field results payload
        field_results_data = [
            {
                "field_id": f.field_id,
                "field_name": f.field_name,
                "status": f.status,
                "found": f.found,
                "matched_text": f.matched_text,
                "confidence_score": f.confidence_score,
                "flag": f.flag,
                "details": f.details
            }
            for f in report.fields
        ]

        now_iso = datetime.now(timezone.utc).isoformat()

        row_data: Dict[str, Any] = {
            "scan_ref_id": report.scan_id,
            "timestamp": now_iso,
            "filename": report.filename or "uploaded_label.png",
            "status": status_val,
            "fields_passed": fields_passed,
            "fields_total": fields_total,
            "field_results": field_results_data
        }

        # 1. Always record in local memory buffer
        _memory_scans.insert(0, row_data)
        if len(_memory_scans) > 100:
            _memory_scans.pop()

        # 2. Try inserting to Supabase if configured
        client = get_supabase_client()
        if client:
            client.table("scans").insert(row_data).execute()
            logger.info(f"[DB] Saved scan record '{report.scan_id}' to Supabase 'scans' table.")
            return True

        return True

    except Exception as e:
        logger.error(f"[DB Error] Supabase write failed for scan '{report.scan_id}': {e}. Returning scan result normally.")
        return False


def get_scans_summary() -> Dict[str, int]:
    """
    Returns aggregate counts: total, compliant, non_compliant, exempt, uncertain.
    Queries Supabase if available; otherwise returns in-memory counts.
    """
    client = get_supabase_client()
    if client:
        try:
            res = client.table("scans").select("status").execute()
            rows = res.data or []
            total = len(rows)
            compliant = sum(1 for r in rows if r.get("status") == "compliant")
            non_compliant = sum(1 for r in rows if r.get("status") == "non-compliant")
            exempt = sum(1 for r in rows if r.get("status") == "exempt")
            uncertain = sum(1 for r in rows if r.get("status") == "uncertain")
            return {
                "total": total,
                "compliant": compliant,
                "non_compliant": non_compliant,
                "exempt": exempt,
                "uncertain": uncertain
            }
        except Exception as e:
            logger.warning(f"[DB] Supabase summary query failed: {e}. Falling back to in-memory counts.")

    # In-memory fallback
    total = len(_memory_scans)
    compliant = sum(1 for r in _memory_scans if r.get("status") == "compliant")
    non_compliant = sum(1 for r in _memory_scans if r.get("status") == "non-compliant")
    exempt = sum(1 for r in _memory_scans if r.get("status") == "exempt")
    uncertain = sum(1 for r in _memory_scans if r.get("status") == "uncertain")
    return {
        "total": total,
        "compliant": compliant,
        "non_compliant": non_compliant,
        "exempt": exempt,
        "uncertain": uncertain
    }


def get_recent_scans(limit: int = 20) -> List[Dict[str, Any]]:
    """
    Returns the most recent scan records (up to limit).
    Queries Supabase if available; otherwise returns in-memory records.
    """
    client = get_supabase_client()
    if client:
        try:
            res = client.table("scans").select("*").order("timestamp", desc=True).limit(limit).execute()
            if res.data:
                return res.data
        except Exception as e:
            logger.warning(f"[DB] Supabase recent scans query failed: {e}. Falling back to in-memory store.")

    # In-memory fallback
    return _memory_scans[:limit]
