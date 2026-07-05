"""
image_handler.py - Image analysis using Gemini Vision API.

Handles image upload, processing (resize/normalise), and intelligent
visual understanding via multimodal Gemini requests.

Supported formats: JPG, JPEG, PNG, WEBP, GIF
"""

import io
from PIL import Image
from google import genai
from google.genai import types
from google.genai import errors as genai_errors

# Vision-capable models in fallback priority order
_VISION_MODELS = [
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
    "gemini-flash-latest",
]

# Map file extensions to MIME types
_MIME_MAP: dict[str, str] = {
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "png": "image/png",
    "webp": "image/webp",
    "gif": "image/gif",
}

# Maximum image dimension for API payload efficiency
_MAX_IMAGE_SIZE = (1024, 1024)


def get_mime_type(filename: str) -> str:
    """
    Return the MIME type string for a given filename.

    Args:
        filename: Uploaded file name (e.g. "photo.png").

    Returns:
        str: MIME type string.
    """
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else "jpeg"
    return _MIME_MAP.get(ext, "image/jpeg")


def process_image(image_bytes: bytes) -> tuple[bytes, str]:
    """
    Resize and normalise an image for efficient API transmission.

    Converts palette/RGBA images to RGB, thumbnails to _MAX_IMAGE_SIZE,
    and re-encodes as JPEG.

    Args:
        image_bytes: Raw uploaded image bytes.

    Returns:
        tuple[bytes, str]: (processed_bytes, mime_type)
    """
    img = Image.open(io.BytesIO(image_bytes))

    # Convert modes incompatible with JPEG to RGB
    if img.mode in ("RGBA", "P", "LA"):
        img = img.convert("RGB")

    # Resize while preserving aspect ratio
    img.thumbnail(_MAX_IMAGE_SIZE, Image.LANCZOS)

    output = io.BytesIO()
    img.save(output, format="JPEG", quality=85, optimize=True)
    return output.getvalue(), "image/jpeg"


def _is_retryable(exc: Exception) -> bool:
    """Return True for transient 429/503 errors."""
    if isinstance(exc, (genai_errors.ServerError, genai_errors.ClientError)):
        return getattr(exc, "status_code", None) in (429, 503)
    msg = str(exc)
    return "503" in msg or "429" in msg or "RESOURCE_EXHAUSTED" in msg


def analyze_image(
    client: genai.Client,
    image_bytes: bytes,
    mime_type: str,
    user_prompt: str = "",
) -> str:
    """
    Send an image to Gemini Vision and return its analysis.

    Args:
        client: Authenticated google.genai Client.
        image_bytes: Processed image bytes.
        mime_type: MIME type of the image.
        user_prompt: Optional question or instruction about the image.

    Returns:
        str: Gemini's textual analysis of the image.

    Raises:
        RuntimeError: If all vision models fail.
    """
    # Default prompt if the user didn't ask anything specific
    prompt_text = user_prompt.strip() or (
        "Describe this image in detail. Include: what you see, objects, colors, "
        "any text present, the setting, and the overall context or mood."
    )

    # Build multimodal content: image blob + text instruction
    parts = [
        types.Part(
            inline_data=types.Blob(mime_type=mime_type, data=image_bytes)
        ),
        types.Part(text=prompt_text),
    ]
    contents = [types.Content(role="user", parts=parts)]

    last_exc: Exception | None = None
    for model in _VISION_MODELS:
        try:
            response = client.models.generate_content(
                model=model,
                contents=contents,
                config=types.GenerateContentConfig(max_output_tokens=8192),
            )
            return response.text
        except Exception as exc:
            if _is_retryable(exc):
                last_exc = exc
                continue
            raise

    raise RuntimeError(f"Image analysis failed across all models. Last error: {last_exc}")
