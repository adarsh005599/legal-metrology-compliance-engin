import io
import os
import re
import json
import base64
import logging
from typing import List, Tuple, Optional, Any
from PIL import Image
import numpy as np
from dotenv import load_dotenv

load_dotenv()

os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"

from app.models import OCRLine, LayoutRegion

logger = logging.getLogger("compliance_engine.ocr")

_ocr_engine = None
_last_scan_cache: dict = {}

# NVIDIA NIM API Configuration (Fallback / Cloud option)
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
NVIDIA_VISION_MODEL = os.environ.get("NVIDIA_VISION_MODEL", "meta/llama-3.2-11b-vision-instruct")


def get_ocr_engine():
    """
    Lazy initialization of PaddleOCR engine with angle classification and English language.
    """
    global _ocr_engine
    if _ocr_engine is None:
        try:
            from paddleocr import PaddleOCR
            logger.info("Initializing PaddleOCR (use_angle_cls=True, lang='en')...")
            _ocr_engine = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
            logger.info("PaddleOCR initialized successfully.")
        except Exception as e:
            logger.warning(f"PaddleOCR not available or failed to load: {e}")
            _ocr_engine = None
    return _ocr_engine


def _get_nvidia_client():
    """Create an OpenAI-compatible client pointing at NVIDIA NIM."""
    from openai import OpenAI
    api_key = os.environ.get("NVIDIA_API_KEY")
    if not api_key:
        raise ValueError(
            "NVIDIA_API_KEY environment variable is not set. "
            "Please set it in your .env file."
        )
    return OpenAI(base_url=NVIDIA_BASE_URL, api_key=api_key)


def _image_to_base64(image_bytes: bytes) -> str:
    """Convert raw image bytes to a base64-encoded data URI for the vision API."""
    return base64.b64encode(image_bytes).decode("utf-8")


EXTRACTION_PROMPT = """You are an OCR engine for product labels. Analyze this image carefully.

TASK 1 — TEXT EXTRACTION:
Extract every single line of visible text from this product/packaging label image, exactly as it appears. Do NOT paraphrase or summarize.

TASK 2 — LAYOUT REGIONS:
Identify major layout sections on the label (e.g. "title", "nutritional_info", "ingredients", "manufacturer_info", "barcode", "table", "figure").

Return your answer as valid JSON with this exact structure (no markdown, no code fences):
{
  "lines": [
    {"text": "exact text of line 1"},
    {"text": "exact text of line 2"}
  ],
  "regions": [
    {"region_type": "title", "text": "Brand Name XYZ"},
    {"region_type": "nutritional_info", "text": "Energy 100kcal Protein 5g..."}
  ]
}

RULES:
- Return ONLY the JSON object, nothing else.
- Do not wrap in markdown code fences.
- Extract ALL text, including small print, legal declarations, weights, prices, dates, addresses.
- For regions, combine text within each region into a single string."""


def _call_nvidia_vision(image_bytes: bytes) -> dict:
    """Send image to NVIDIA NIM vision model and parse the JSON response."""
    client = _get_nvidia_client()
    b64_image = _image_to_base64(image_bytes)

    response = client.chat.completions.create(
        model=NVIDIA_VISION_MODEL,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": EXTRACTION_PROMPT,
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{b64_image}",
                        },
                    },
                ],
            }
        ],
        max_tokens=4096,
        temperature=0.0,
        timeout=15.0,
    )

    raw_text = response.choices[0].message.content.strip()
    raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
    raw_text = re.sub(r"\s*```$", "", raw_text)

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse NVIDIA response as JSON: {e}\nRaw: {raw_text[:500]}")
        parsed = {
            "lines": [{"text": line.strip()} for line in raw_text.splitlines() if line.strip()],
            "regions": [],
        }

    return parsed


def _extract_with_paddle(image: Image.Image) -> Tuple[List[OCRLine], List[str]]:
    """Runs PaddleOCR on a PIL image and extracts text lines and bounding boxes."""
    engine = get_ocr_engine()
    if engine is None:
        raise RuntimeError("PaddleOCR engine not initialized.")

    img_np = np.array(image)
    result = None
    try:
        result = engine.ocr(img_np, cls=True)
    except (TypeError, Exception) as call_err:
        if "cls" in str(call_err) or isinstance(call_err, TypeError):
            result = engine.ocr(img_np)
        else:
            raise call_err

    ocr_lines: List[OCRLine] = []
    text_lines: List[str] = []

    if result and len(result) > 0 and result[0] is not None:
        lines_data = result[0] if isinstance(result[0], list) else result
        for item in lines_data:
            try:
                if isinstance(item, (list, tuple)) and len(item) >= 2:
                    bbox = item[0] if isinstance(item[0], list) else None
                    if isinstance(item[1], (tuple, list)) and len(item[1]) >= 2:
                        text_content = str(item[1][0]).strip()
                        confidence = float(item[1][1])
                    else:
                        text_content = str(item[1]).strip()
                        confidence = 0.95
                elif isinstance(item, dict):
                    text_content = str(item.get("text", "")).strip()
                    confidence = float(item.get("confidence", item.get("score", 0.95)))
                    bbox = item.get("bbox", None)
                else:
                    continue

                if text_content:
                    ocr_lines.append(OCRLine(
                        text=text_content,
                        confidence=confidence,
                        bbox=bbox
                    ))
                    text_lines.append(text_content)
            except (IndexError, TypeError, ValueError) as parse_err:
                logger.warning(f"Skipping malformed OCR line result: {item}, error: {parse_err}")
                continue

    return ocr_lines, text_lines


def extract_text_from_bytes(image_bytes: bytes) -> Tuple[List[OCRLine], List[str]]:
    """
    Extracts text lines and confidence scores from raw image bytes.
    Uses PaddleOCR locally as the primary engine; falls back to Vision API if configured.
    """
    try:
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception as e:
        logger.error(f"Failed to decode image bytes: {e}")
        raise ValueError(f"Invalid image format: {e}")

    # 1. Try PaddleOCR first
    try:
        ocr_lines, text_lines = _extract_with_paddle(image)
        if ocr_lines:
            _last_scan_cache["ocr_lines"] = ocr_lines
            _last_scan_cache["text_lines"] = text_lines
            return ocr_lines, text_lines
    except Exception as paddle_err:
        logger.warning(f"PaddleOCR extraction failed: {paddle_err}. Attempting fallback...")

    # 2. Vision API fallback if NVIDIA_API_KEY is present
    if os.environ.get("NVIDIA_API_KEY"):
        try:
            parsed = _call_nvidia_vision(image_bytes)
            _last_scan_cache["parsed"] = parsed

            ocr_lines: List[OCRLine] = []
            text_lines: List[str] = []

            for item in parsed.get("lines", []):
                text = item.get("text", "").strip()
                if text:
                    ocr_lines.append(
                        OCRLine(
                            text=text,
                            confidence=0.98,
                            bbox=None,
                        )
                    )
                    text_lines.append(text)
            if ocr_lines:
                return ocr_lines, text_lines
        except Exception as vision_err:
            logger.error(f"NVIDIA Vision API fallback failed: {vision_err}")

    # 3. If nothing succeeded
    return [], []


def analyze_layout_from_bytes(image_bytes: bytes) -> List[LayoutRegion]:
    """
    Extracts structural layout blocks from OCR lines or cached vision response.
    """
    # If vision response is cached
    parsed = _last_scan_cache.get("parsed")
    if parsed and parsed.get("regions"):
        regions: List[LayoutRegion] = []
        for reg in parsed.get("regions", []):
            regions.append(
                LayoutRegion(
                    region_type=reg.get("region_type", "unknown"),
                    bbox=[],
                    text=reg.get("text", ""),
                )
            )
        return regions

    # Inferred layout regions from OCR lines
    ocr_lines = _last_scan_cache.get("ocr_lines")
    if not ocr_lines:
        try:
            ocr_lines, _ = extract_text_from_bytes(image_bytes)
        except Exception:
            ocr_lines = []

    regions: List[LayoutRegion] = []
    if not ocr_lines:
        return regions

    title_lines = []
    nutri_lines = []
    mfr_lines = []
    decl_lines = []

    for idx, l in enumerate(ocr_lines):
        t_lower = l.text.lower()
        if any(k in t_lower for k in ["protein", "fat", "carbohydrate", "energy", "kcal", "sodium", "nutrition", "ingredients"]):
            nutri_lines.append(l.text)
        elif any(k in t_lower for k in ["mfd by", "manufactured", "packed by", "marketed by"]):
            mfr_lines.append(l.text)
        elif any(k in t_lower for k in ["mrp", "net wt", "net weight", "mfd:", "customer care", "helpline"]):
            decl_lines.append(l.text)
        elif idx == 0 or (idx == 1 and not title_lines):
            title_lines.append(l.text)
        else:
            decl_lines.append(l.text)

    if title_lines:
        regions.append(LayoutRegion(region_type="title", text=" | ".join(title_lines)))
    if decl_lines:
        regions.append(LayoutRegion(region_type="legal_declarations", text=" | ".join(decl_lines)))
    if mfr_lines:
        regions.append(LayoutRegion(region_type="manufacturer_info", text=" | ".join(mfr_lines)))
    if nutri_lines:
        regions.append(LayoutRegion(region_type="nutritional_info", text=" | ".join(nutri_lines)))

    return regions
