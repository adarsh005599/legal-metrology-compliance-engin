import io
import os
import logging

os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"
from typing import List, Tuple, Optional
from PIL import Image
import numpy as np
from app.models import OCRLine

logger = logging.getLogger("compliance_engine.ocr")

_ocr_engine = None

def get_ocr_engine():
    """
    Lazy initialization of PaddleOCR engine with angle classification and English language.
    """
    global _ocr_engine
    if _ocr_engine is None:
        try:
            from paddleocr import PaddleOCR
            logger.info("Initializing PaddleOCR (use_angle_cls=True, lang='en')...")
            _ocr_engine = PaddleOCR(use_angle_cls=True, lang='en')
            logger.info("PaddleOCR initialized successfully.")
        except Exception as e:
            logger.error(f"Error initializing PaddleOCR: {e}")
            raise e
    return _ocr_engine


def extract_text_from_bytes(image_bytes: bytes) -> Tuple[List[OCRLine], List[str]]:
    """
    Extracts text lines and confidence scores from raw image bytes using PaddleOCR.
    Handles multiple PaddleOCR API versions seamlessly (v2.x, v3.x).
    """
    try:
        # Load image with PIL and convert to RGB numpy array
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        img_np = np.array(image)
    except Exception as e:
        logger.error(f"Failed to decode image bytes: {e}")
        raise ValueError(f"Invalid image format: {e}")

    engine = get_ocr_engine()
    
    # Run PaddleOCR with multi-version fallback (cls=True vs direct call)
    result = None
    try:
        try:
            result = engine.ocr(img_np, cls=True)
        except (TypeError, Exception) as call_err:
            if "cls" in str(call_err) or isinstance(call_err, TypeError):
                result = engine.ocr(img_np)
            else:
                raise call_err
    except Exception as e:
        logger.error(f"PaddleOCR execution failed: {e}")
        raise RuntimeError(f"OCR processing failed: {e}")

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
