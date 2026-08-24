---
title: Legal Metrology Compliance Assist Engine
emoji: ⚖️
colorFrom: blue
colorTo: indigo
sdk: docker
app_port: 7860
pinned: false
license: mit
---

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
1. **Maximum Retail Price (MRP)**: Matches `MRP`, `M.R.P.`, `Maximum Retail Price` followed by a valid Indian rupee amount on the same or adjacent line. Flags dual-pricing contradictions and price stickers.
2. **Net Quantity**: Matches net quantity with valid standard SI units (`g`, `kg`, `ml`, `l`). Flags non-standard units (e.g. `gm`, `gms`).
3. **Date of Manufacture / Packing**: Validates month/year formats (`MM/YYYY`, `MM/YY`, `MMM YYYY`).
4. **Manufacturer / Packer Name & Address**: Validates postal keywords, pin codes, and multi-line addresses.
5. **Consumer Care Details**: Validates phone numbers, helplines, email addresses, and grievance contacts.

---

## 🛠️ Tech Stack
- **Backend**: FastAPI, Uvicorn, Pydantic v2
- **OCR Engine**: PaddleOCR v2.7+ (CPU optimized)
- **Database & Sync**: Supabase PostgreSQL + Fallback In-Memory Buffer
- **PDF Report Generation**: ReportLab
- **Frontend**: Responsive HTML5, Vanilla JavaScript, Chart.js, Custom CSS

---

## 🏁 Quickstart

```powershell
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run backend server
uvicorn main:app --reload

# 3. Open browser
http://127.0.0.1:8000
```
