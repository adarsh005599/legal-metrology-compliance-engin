# MetraSetu: Dependencies & System Requirements Specification

This document provides a comprehensive inventory of all **Python backend dependencies**, **Linux/Docker runtime system libraries**, **client-side frontend assets**, and **environment variables** required to build, test, and deploy the **MetraSetu: Legal Metrology Compliance Assistant**.

---

## 1. Python Backend Dependencies (`requirements.txt`)

| Package Name | Version Constraint | Category | Architectural Role & Purpose |
|---|---|---|---|
| **`fastapi`** | `>=0.110.0` | API Framework | High-performance asynchronous REST API framework serving label scanning, dashboard telemetry, and health probe endpoints. |
| **`uvicorn[standard]`** | `>=0.28.0` | ASGI Server | Production-ready asynchronous web server with standard WebSocket and event loop loop implementations (`uvloop`/`httptools`). |
| **`python-multipart`** | `>=0.0.9` | Request Parser | Multipart form-data streaming parser for processing high-resolution image uploads. |
| **`paddleocr`** | `>=2.7.0` | Computer Vision | Edge-native OCR engine combining **DBNet** (text detection), **Angle Classifier**, and **SVTR_LCNet** (character recognition). |
| **`paddlepaddle`** | `>=2.5.0` | Deep Learning Backend | Core tensor and neural network computation graph engine powering PaddleOCR models. |
| **`opencv-python-headless`**| `>=4.8.0` | Image Processing | Headless computer vision library providing image cropping, filtering, and normalization without GUI X11 dependencies. |
| **`reportlab`** | `>=4.1.0` | Document Generation | Engine for generating official, downloadable PDF compliance screening reports with statutory framing. |
| **`pydantic`** | `>=2.6.0` | Data Validation | Strict type safety and schema validation for API request/response models (`OCRLine`, `RuleResult`, `ComplianceReport`). |
| **`pillow`** | `>=10.0.0` | Imaging | Image reading, format conversion, and Lanczos downscaling for memory-efficient inference. |
| **`numpy`** | `>=1.24.0, <2.0.0`| Numerical Computing | High-performance multidimensional arrays and matrix manipulations for image tensors. |
| **`supabase`** | `>=2.30.0` | Database Client | Cloud database client for persisting screening records, verdict summaries, and historical telemetry. |
| **`python-dotenv`** | `>=1.0.0` | Configuration | Loads configuration settings from `.env` files into environment variables for local development. |

---

## 2. Linux / Container System Packages (`Dockerfile` / `nixpacks.toml`)

These native C/C++ runtime shared libraries must be present on Debian/Ubuntu, Docker, or Railway/Render container environments:

```bash
# Debian / Ubuntu / Docker base installation
apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*
```

### System Library Explanations:
1. **`libgl1` (Mesa OpenGL Runtime):**
   - Required by OpenCV core graphics and image decompression routines.
2. **`libglib2.0-0` (GLib Core Runtime):**
   - Fundamental C library providing low-level data structures, threads, and dynamic loading needed by image processing toolkits.
3. **`libgomp1` (GNU OpenMP Runtime):**
   - Multi-threading acceleration library enabling multi-core CPU parallelism for PaddlePaddle neural network tensor operations.
4. **`curl`:**
   - Command-line HTTP tool utilized by container orchestrators for liveness and readiness health probes.

---

## 3. Frontend & Client-Side Assets (100% Self-Hosted & Offline Capable)

| Asset / Technology | Local File Path | Purpose |
|---|---|---|
| **Chart.js Bundle** | `app/static/chart.umd.min.js` (v4.4.2) | Visualizes compliance ratios (doughnut) and scan volume metrics (bar chart) without external CDN or Cloudflare dependencies. |
| **Bilingual i18n Engine** | `app/static/i18n.js` | Native client-side dictionary for instantaneous one-click English $\leftrightarrow$ Hindi (हिन्दी) UI switching with zero reload. |
| **Liquid Glass Stylesheet** | `app/static/style.css` | Custom CSS3 theme incorporating frosted glassmorphism, responsive viewports, and calibration aesthetics. |
| **Application Logic** | `app/static/app.js` | Client-side controller managing file uploads, WebRTC camera viewfinder, laser sweeps, and dynamic result rendering. |
| **Dashboard Controller** | `app/static/dashboard.js` | Manages real-time search filtering, category pills, telemetry synchronization, and Chart.js instances. |
| **Typography Fonts** | Google Fonts Link | `IBM Plex Sans` (UI), `IBM Plex Mono` (Calibrated numerical readouts), and `Noto Sans Devanagari` (Hindi text). |
| **Browser Native APIs** | Native HTML5 / ES2022 | `navigator.mediaDevices.getUserMedia` (WebRTC), HTML5 Canvas API, and `localStorage` state persistence. |

---

## 4. Environment Variables Specification (`.env`)

| Variable | Required | Default | Description |
|---|:---:|---|---|
| **`PORT`** | No | `8000` | Port on which the FastAPI/Uvicorn server listens (automatically injected by Railway, Render, and Hugging Face). |
| **`PYTHONUNBUFFERED`** | No | `1` | Forces standard output and error streams to be unbuffered for instant container logging. |
| **`SUPABASE_URL`** | No | `None` | Cloud PostgreSQL REST endpoint for logging inspection telemetry. |
| **`SUPABASE_KEY`** | No | `None` | API key (anon or service role) for authenticating Supabase client writes. |

---

## 5. Quick Installation & Setup

### Local Python Environment:
```bash
# 1. Clone repository
git clone https://github.com/adarsh005599/legal-metrology-compliance-engin.git
cd legal-metrology-compliance-engin

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start local development server
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### Docker Container Build:
```bash
docker build -t metrasetu:latest .
docker run -p 8000:8000 metrasetu:latest
```
