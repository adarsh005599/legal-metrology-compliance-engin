import io
import os
import re
import json
import base64
import logging
from typing import List, Tuple, Optional
from PIL import Image
from openai import OpenAI

from app.models import OCRLine, LayoutRegion

logger = logging.getLogger("compliance_engine.ocr")

# NVIDIA NIM API Configuration
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
NVIDIA_VISION_MODEL = "meta/llama-3.2-90b-vision-instruct"

def _get_nvidia_client() -> OpenAI:
    """Create an OpenAI-compatible client pointing at NVIDIA NIM."""
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
    )

    raw_text = response.choices[0].message.content.strip()

    # Strip markdown code fences if the model wraps its output
    raw_text = re.sub(r"^```(?:json)?\s*", "", raw_text)
    raw_text = re.sub(r"\s*```$", "", raw_text)

    try:
        parsed = json.loads(raw_text)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse NVIDIA response as JSON: {e}\nRaw: {raw_text[:500]}")
        # Fallback: treat entire response as a single text line
        parsed = {
            "lines": [{"text": line.strip()} for line in raw_text.splitlines() if line.strip()],
            "regions": [],
        }

    return parsed


# ---------------------------------------------------------------------------
# Cache: avoid calling the API twice per upload (extract_text + analyze_layout)
# ---------------------------------------------------------------------------
_last_scan_cache: dict = {}


def extract_text_from_bytes(image_bytes: bytes) -> Tuple[List[OCRLine], List[str]]:
    """
    Extracts text lines from raw image bytes using NVIDIA NIM Vision API.
    Returns (list of OCRLine, list of raw text strings).
    """
    try:
        Image.open(io.BytesIO(image_bytes)).convert("RGB")
    except Exception as e:
        logger.error(f"Failed to decode image bytes: {e}")
        raise ValueError(f"Invalid image format: {e}")

    parsed = _call_nvidia_vision(image_bytes)

    # Store in cache for analyze_layout_from_bytes
    _last_scan_cache["parsed"] = parsed

    ocr_lines: List[OCRLine] = []
    text_lines: List[str] = []

    for item in parsed.get("lines", []):
        text = item.get("text", "").strip()
        if text:
            ocr_lines.append(
                OCRLine(
                    text=text,
                    confidence=1.0,
                    bbox=None,
                )
            )
            text_lines.append(text)

    return ocr_lines, text_lines


def analyze_layout_from_bytes(image_bytes: bytes) -> List[LayoutRegion]:
    """
    Extracts structural layout blocks from cached NVIDIA response.
    Falls back to a fresh API call if the cache is empty.
    """
    parsed = _last_scan_cache.get("parsed")

    if not parsed:
        logger.warning("Cache miss in analyze_layout_from_bytes. Calling NVIDIA again.")
        parsed = _call_nvidia_vision(image_bytes)

    regions: List[LayoutRegion] = []
    for reg in parsed.get("regions", []):
        regions.append(
            LayoutRegion(
                region_type=reg.get("region_type", "unknown"),
                bbox=[],
                text=reg.get("text", ""),
            )
        )

    # Clear cache after use
    _last_scan_cache.clear()

    return regions
