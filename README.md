# Legal Metrology Compliance-Assist Engine
**Smart India Hackathon (SIH PS-26034)**  
*Target Ministry: Ministry of Consumer Affairs, Food & Public Distribution*

---

## ⚖️ Critical Statutory Framing Notice
> **Statutory Notice:** *This is a compliance-assist screening report, not a statutory notice under the Legal Metrology Act, 2009.*
>
> Under Section 15 of the Legal Metrology Act, 2009, statutory power to issue inspection notices, seize packaged commodities, or initiate legal proceedings is exclusively vested with designated government **Legal Metrology Officers (LMO)**. This software functions strictly as an automated **pre-inspection screening tool** to assist compliance verification.

---

## 🚀 Overview & Architecture

The **Legal Metrology Compliance-Assist Engine** is an end-to-end web system designed to rapidly screen packaged commodity labels against mandatory declarations under the **Legal Metrology (Packaged Commodities) Rules, 2011**.

```
[ Uploaded Label Image ]
           │
           ▼
[ Feature 1: PaddleOCR Pipeline ] ──► Extracts text lines & confidence
           │
           ▼
[ Feature 2: Statutory Exemption Filter ] (Rule 3 & Rule 26)
           │
     ┌─────┴───────────────────────┐
     │ Is Exempt?                  │
    YES                            NO
     │                             │
     ▼                             ▼
[ Return "EXEMPT" ]      [ Feature 3: Rule Engine (5 Fields) ]
(Waives declarations)     1. MRP & Dual-Pricing Anomaly (Rule 6(1)(e))
                          2. Net Quantity & SI Units (Rule 6(1)(b) & Rule 12)
                          3. Date of Mfg / Packing (Rule 6(1)(d))
                          4. Manufacturer / Packer Address (Rule 6(1)(a))
                          5. Consumer Care Details (Rule 6(1)(f))
                                   │
                                   ▼
                   [ Feature 4: ReportLab PDF Generator ]
                   [ Feature 5: Interactive Web UI ]
```

---

## 📦 Features Implemented

### 1. OCR Pipeline (`app/engine/ocr.py`)
- Utilizes **PaddleOCR** with `use_angle_cls=True, lang='en'`.
- Extracts detected text lines, bounding coordinates, and confidence scores.
- Scope consideration: Assumes flat, reasonably well-lit labels without heavyweight perspective correction.

### 2. Statutory Exemption Filter (`app/engine/exemption.py`)
Evaluated **before** rule checking under Rule 3 and Rule 26:
- **Condition 1**: "Not for retail sale" / Institutional supply.
- **Condition 2**: Package weight > 25 kg or volume > 25 L (threshold extended up to 50 kg for cement and fertilizer packages).
- **Condition 3**: Net quantity ≤ 10 g or ≤ 10 ml (**strictly excluded** if tobacco is detected, as tobacco is never exempt under Rule 26).
- **Condition 4**: Openly sold / loose goods weighed at counter.

### 3. Rule Engine — 5 Mandatory Fields (`app/engine/rules.py`)
- **Field 1: MRP**: Regex validation for rupee pricing near MRP keywords. Flags dual pricing and price-sticker alteration anomalies.
- **Field 2: Net Quantity**: Standard SI unit validation (`g`, `kg`, `ml`, `l`). Non-standard units (`gm`, `gms`, `ltr`) are flagged with a warning rather than rejected.
- **Field 3: Month & Year of Mfg/Packing**: Regex matching for date patterns near `mfg`, `mfd`, `pkd`, `packed`.
- **Field 4: Manufacturer / Packer Address**: Matches `mfd by`, `marketed by`, `packed by` followed by address text.
- **Field 5: Consumer Care Details**: Matches 10-digit telephone numbers, toll-free lines (`1800-xxx-xxxx`), or email addresses.

### 4. PDF Report Generation (`app/engine/pdf_report.py`)
- Generates downloadable `Compliance_Assist_Report_<ScanID>.pdf` using **ReportLab**.
- Formatted with Ministry styling, scan metadata, exemption status, 5-field compliance table, OCR preview, and statutory Section 15 disclaimer box.

### 5. Frontend (`app/static/`)
- Single-page application with drag-and-drop file upload, live image preview, and 1-click test presets for hackathon demonstrations.
- Visual badges: **PASS (Green)**, **FAIL (Red)**, **FLAGGED (Amber)**, **EXEMPT (Blue)**.
- Direct PDF report export button.

---

## 🛠️ Tech Stack
- **Backend**: Python 3.10+, FastAPI, Uvicorn
- **OCR**: PaddleOCR, PaddlePaddle
- **PDF Engine**: ReportLab
- **Frontend**: Vanilla HTML5, CSS3, JavaScript (no complex build step required)
- **Validation**: Pydantic v2

---

## ⚙️ Installation & Setup

### 1. Clone or Open Workspace
```bash
cd "Legal Metrology Compliance-Assist Engine"
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Start the Web Application
```bash
uvicorn main:app --reload
```

### 4. Open in Browser
Visit **[http://127.0.0.1:8000](http://127.0.0.1:8000)** in any web browser.

---

## 🧪 Running Unit Tests & Batch Self-Test

### Run Automated Unit & Integration Tests:
```bash
python -m unittest discover -s tests
```

### Run Batch Self-Test Suite on `/data/sample_labels`:
```bash
python scripts/batch_test.py data/sample_labels
```
*(Prints a full summary table and exports results to `batch_test_results.csv`)*

---

## 📡 API Reference

### `POST /api/scan`
- **Payload**: `multipart/form-data` with `file: <image file>`
- **Response**: `ComplianceReport` JSON object

### `POST /api/scan-text`
- **Payload**: `{"text": "...", "filename": "sample.jpg"}`
- **Response**: `ComplianceReport` JSON object (for headless evaluation/testing)

### `POST /api/export`
- **Payload**: `ComplianceReport` JSON object
- **Response**: Binary stream of PDF document (`application/pdf`)

---

## 🚫 Explicit Out-of-Scope (MVP Scope Boundaries)
The following items are intentionally excluded from this hackathon MVP and listed for future work:
- Unit sale price (USP) calculation
- Country of origin declaration check
- Font size / legibility / aspect ratio measurement
- FSSAI license / food safety declarations
- Multi-photo 360-degree bottle stitching
- Cloud/local Large Language Model (LLM) pipelines (pure deterministic regex used)
- User authentication and persistent databases
