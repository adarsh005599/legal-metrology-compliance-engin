import os
import uuid
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any

from fastapi import FastAPI, File, UploadFile, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, FileResponse
from fastapi.staticfiles import StaticFiles

from app.models import ComplianceReport, ExemptionResult, MANDATORY_DISCLAIMER
from app.engine.ocr import extract_text_from_bytes
from app.engine.exemption import check_exemptions
from app.engine.rules import evaluate_all_rules
from app.engine.pdf_report import generate_pdf_report
from app.db.supabase_client import save_scan_record, get_scans_summary, get_recent_scans

logger = logging.getLogger("legal_metrology.api")

app = FastAPI(
    title="Legal Metrology Compliance-Assist Engine",
    description="Pre-inspection screening report API for packaged commodity compliance (Ministry of Consumer Affairs, Food & Public Distribution)",
    version="1.0.0"
)

# Enable CORS for frontend flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_warmup():
    """
    Pre-warm PaddleOCR engine on server boot to eliminate first-request latency.
    """
    logger.info("Pre-warming PaddleOCR engine on server startup...")
    try:
        from app.engine.ocr import get_ocr_engine
        import numpy as np
        engine = get_ocr_engine()
        dummy = np.zeros((100, 100, 3), dtype=np.uint8)
        try:
            engine.ocr(dummy, cls=True)
        except Exception:
            engine.ocr(dummy)
        logger.info("PaddleOCR engine pre-warmed successfully.")
    except Exception as e:
        logger.warning(f"PaddleOCR startup warmup notice: {e}")


@app.post("/api/scan", response_model=ComplianceReport)
async def scan_label(file: UploadFile = File(...)):
    """
    Accepts an uploaded label image (JPEG/PNG), extracts text using PaddleOCR,
    evaluates statutory exemptions under Rule 3 & 26, and (if not exempt)
    evaluates the 5 mandatory Legal Metrology declaration fields.
    """
    if not file.content_type or not (file.content_type.startswith("image/") or file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.bmp'))):
        raise HTTPException(status_code=400, detail="Uploaded file must be a valid image (PNG or JPEG).")

    try:
        image_bytes = await file.read()
        if len(image_bytes) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read upload: {str(e)}")

    # 1. OCR Extraction
    try:
        ocr_lines, text_lines = extract_text_from_bytes(image_bytes)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OCR engine failed to process image: {str(e)}")

    scan_id = f"LM-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    timestamp_str = datetime.now().strftime("%d-%m-%Y %H:%M:%S IST")
    raw_text = "\n".join(text_lines)

    # 2. Exemption Filter (Rule 3 & Rule 26) - Checked BEFORE compliance rules
    exemption_result = check_exemptions(ocr_lines)

    if exemption_result.is_exempt:
        report = ComplianceReport(
            scan_id=scan_id,
            timestamp=timestamp_str,
            filename=file.filename,
            is_exempt=True,
            exemption_details=exemption_result,
            overall_status="EXEMPT",
            fields=[],
            extracted_lines=ocr_lines,
            raw_text=raw_text,
            disclaimer=MANDATORY_DISCLAIMER
        )
        try:
            save_scan_record(report)
        except Exception as db_err:
            logger.warning(f"Non-blocking DB write error: {db_err}")
        return report

    # 3. Rule Engine: 5 Mandatory Declaration Fields with OCR confidence auditing
    fields = evaluate_all_rules(ocr_lines)
    
    # Overall status determination:
    has_failure = any(f.status == "FAIL" for f in fields)
    has_warning = any(f.status == "WARNING" for f in fields)
    has_uncertain = any(f.status == "UNCERTAIN" for f in fields)

    if has_failure or has_warning:
        overall_status = "NON_COMPLIANT"
    elif has_uncertain:
        overall_status = "UNCERTAIN"
    else:
        overall_status = "COMPLIANT"

    report = ComplianceReport(
        scan_id=scan_id,
        timestamp=timestamp_str,
        filename=file.filename,
        is_exempt=False,
        exemption_details=None,
        overall_status=overall_status,
        fields=fields,
        extracted_lines=ocr_lines,
        raw_text=raw_text,
        disclaimer=MANDATORY_DISCLAIMER
    )

    # Async / Non-blocking save to Supabase
    try:
        save_scan_record(report)
    except Exception as db_err:
        logger.warning(f"Non-blocking DB write error: {db_err}")

    return report


@app.post("/api/scan-text", response_model=ComplianceReport)
async def scan_raw_text(payload: dict = Body(...)):
    """
    Direct text scanning endpoint for automated testing / headless evaluation.
    Payload: {"text": "MRP Rs. 100 ...", "filename": "sample_label.jpg"}
    """
    input_text = payload.get("text", "")
    filename = payload.get("filename", "text_input.txt")
    text_lines = [line.strip() for line in input_text.splitlines() if line.strip()]
    if not text_lines and input_text:
        text_lines = [input_text]

    scan_id = f"LM-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
    timestamp_str = datetime.now().strftime("%d-%m-%Y %H:%M:%S IST")

    exemption_result = check_exemptions(text_lines)

    if exemption_result.is_exempt:
        report = ComplianceReport(
            scan_id=scan_id,
            timestamp=timestamp_str,
            filename=filename,
            is_exempt=True,
            exemption_details=exemption_result,
            overall_status="EXEMPT",
            fields=[],
            extracted_lines=[],
            raw_text=input_text,
            disclaimer=MANDATORY_DISCLAIMER
        )
        try:
            save_scan_record(report)
        except Exception as db_err:
            logger.warning(f"Non-blocking DB write error: {db_err}")
        return report

    fields = evaluate_all_rules(text_lines)
    has_failure = any(f.status == "FAIL" for f in fields)
    has_warning = any(f.status == "WARNING" for f in fields)
    has_uncertain = any(f.status == "UNCERTAIN" for f in fields)
    
    if has_failure or has_warning:
        overall_status = "NON_COMPLIANT"
    elif has_uncertain:
        overall_status = "UNCERTAIN"
    else:
        overall_status = "COMPLIANT"

    report = ComplianceReport(
        scan_id=scan_id,
        timestamp=timestamp_str,
        filename=filename,
        is_exempt=False,
        exemption_details=None,
        overall_status=overall_status,
        fields=fields,
        extracted_lines=[],
        raw_text=input_text,
        disclaimer=MANDATORY_DISCLAIMER
    )

    try:
        save_scan_record(report)
    except Exception as db_err:
        logger.warning(f"Non-blocking DB write error: {db_err}")

    return report


@app.get("/api/scans/summary")
async def api_scans_summary():
    """
    Returns aggregate compliance metrics: total, compliant, non_compliant, exempt counts.
    """
    try:
        return get_scans_summary()
    except Exception as e:
        logger.warning(f"Error fetching scans summary: {e}")
        return {"total": 0, "compliant": 0, "non_compliant": 0, "exempt": 0, "uncertain": 0}


@app.get("/api/scans/recent")
async def api_scans_recent(limit: int = 20):
    """
    Returns list of the last 20 scans from Supabase (or in-memory cache).
    """
    try:
        return get_recent_scans(limit=limit)
    except Exception as e:
        logger.warning(f"Error fetching recent scans: {e}")
        return []


@app.post("/api/export")
async def export_pdf_report(report: ComplianceReport):
    """
    Accepts a scan result JSON and returns a formatted downloadable PDF report.
    """
    try:
        pdf_bytes = generate_pdf_report(report)
        filename = f"Compliance_Assist_Report_{report.scan_id}.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Access-Control-Expose-Headers": "Content-Disposition"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate PDF report: {str(e)}")


# Mount static directory for frontend
static_dir = os.path.join(os.path.dirname(__file__), "app", "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
async def read_index():
    index_file = os.path.join(static_dir, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    return {"message": "Legal Metrology Compliance-Assist Engine API is running. Place index.html in app/static."}


@app.get("/dashboard")
async def read_dashboard():
    dashboard_file = os.path.join(static_dir, "dashboard.html")
    if os.path.exists(dashboard_file):
        return FileResponse(dashboard_file)
    return {"message": "Dashboard page not found in app/static/dashboard.html."}
