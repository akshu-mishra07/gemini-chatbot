from __future__ import annotations

"""Image persistence, OCR, and history helpers."""

import datetime as dt
import os
import re
from io import BytesIO
from typing import Any

from PIL import Image, ImageOps, ImageFilter, ImageEnhance

from database.storage import execute, fetch_all, now_iso
from document_processor import attempt_image_ocr


IMAGE_HISTORY_DIR = os.path.join("image_history")


def _safe_filename(filename: str) -> str:
    base = os.path.basename(filename)
    return re.sub(r"[^a-zA-Z0-9._-]", "_", base) or "uploaded_image.png"


def extract_ocr_text(file_bytes: bytes, filename: str) -> str:
    try:
        return attempt_image_ocr(file_bytes, filename)
    except Exception:
        return ""


def save_uploaded_image_event(
    *,
    file_bytes: bytes,
    filename: str,
    user_id: str,
    session_id: str,
) -> dict[str, Any]:
    os.makedirs(IMAGE_HISTORY_DIR, exist_ok=True)
    safe_name = _safe_filename(filename)
    stamp = dt.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    path = os.path.join(IMAGE_HISTORY_DIR, f"{stamp}_{safe_name}")

    with open(path, "wb") as f:
        f.write(file_bytes)

    image = Image.open(BytesIO(file_bytes))
    image = ImageOps.exif_transpose(image)
    width, height = image.size
    ocr_text = extract_ocr_text(file_bytes, filename)

    execute(
        """
        INSERT INTO image_events
            (user_id, session_id, filename, path, width, height, ocr_text, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (str(user_id), session_id, filename, path, width, height, ocr_text, now_iso()),
    )

    return {
        "filename": filename,
        "path": path,
        "width": width,
        "height": height,
        "ocr_text": ocr_text,
        "image": image,
    }


def list_image_events(limit: int = 50) -> list[dict[str, Any]]:
    return fetch_all(
        """
        SELECT * FROM image_events
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (limit,),
    )


def edit_image(image: Image.Image, command: str) -> tuple[Image.Image, str] | None:
    """
    Applies a local PIL image transformation based on a natural language command.
    Returns (edited_image, status_message) or None if no match.
    """
    cmd = command.lower().strip()
    
    # 1. Grayscale
    if any(k in cmd for k in ["grayscale", "black and white", "b&w", "black & white"]):
        return image.convert("L").convert("RGB"), "Grayscale filter applied successfully!"
        
    # 2. Rotate
    if "rotate 90" in cmd or "rotate clockwise" in cmd:
        return image.transpose(Image.ROTATE_270), "Rotated 90 degrees clockwise!"
    if "rotate 180" in cmd:
        return image.transpose(Image.ROTATE_180), "Rotated 180 degrees!"
    if "rotate 270" in cmd or "rotate counter-clockwise" in cmd or "rotate counterclockwise" in cmd:
        return image.transpose(Image.ROTATE_90), "Rotated 270 degrees clockwise (90 degrees counter-clockwise)!"
    if "rotate" in cmd:
        return image.transpose(Image.ROTATE_270), "Rotated 90 degrees clockwise!"
        
    # 3. Mirror/Flip
    if "mirror" in cmd or "flip horizontal" in cmd or "flip left right" in cmd:
        return image.transpose(Image.FLIP_LEFT_RIGHT), "Image mirrored horizontally!"
    if "flip vertical" in cmd or "flip top bottom" in cmd or "flip" in cmd:
        return image.transpose(Image.FLIP_TOP_BOTTOM), "Image flipped vertically!"
        
    # 4. Blur
    if "blur" in cmd:
        return image.filter(ImageFilter.BLUR), "Blur filter applied successfully!"
        
    # 5. Invert
    if "invert" in cmd or "negative" in cmd:
        if image.mode != "RGB":
            image = image.convert("RGB")
        return ImageOps.invert(image), "Image colors inverted successfully!"
        
    # 6. Brightness
    if any(k in cmd for k in ["brighten", "make brighter", "increase brightness", "brighter"]):
        enhancer = ImageEnhance.Brightness(image)
        return enhancer.enhance(1.5), "Brightness increased by 50%!"
    if any(k in cmd for k in ["darken", "make darker", "decrease brightness", "darker"]):
        enhancer = ImageEnhance.Brightness(image)
        return enhancer.enhance(0.6), "Brightness decreased by 40%!"
        
    # 7. Contrast
    if any(k in cmd for k in ["increase contrast", "higher contrast", "more contrast"]):
        enhancer = ImageEnhance.Contrast(image)
        return enhancer.enhance(1.5), "Contrast increased by 50%!"
    if any(k in cmd for k in ["decrease contrast", "lower contrast", "less contrast"]):
        enhancer = ImageEnhance.Contrast(image)
        return enhancer.enhance(0.6), "Contrast decreased by 40%!"
        
    return None
