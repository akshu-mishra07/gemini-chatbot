"""
chatbot.py - Gemini API integration module.

Supports:
- Plain text chat with full conversation history
- Multimodal chat (text + image)
- PDF context injection (grounding in document content)
- Custom system prompts (medical / research modes)
- Automatic model fallback on 503 / 429 errors

Uses the latest google.genai SDK exclusively.
"""

import os
from google import genai
from google.genai import types
from google.genai import errors as genai_errors

# Models tried in order — first one available and not rate-limited wins.
_FALLBACK_MODELS = [
    "gemini-2.5-flash-lite",
    "gemini-2.0-flash",
    "gemini-flash-latest",
    "gemini-pro-latest",
]


def get_api_key() -> str:
    """
    Read the Gemini API key from environment variables.

    Returns:
        str: API key string.

    Raises:
        ValueError: If GEMINI_API_KEY is not set.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY environment variable is not set. "
            "Please add it in the Replit Secrets panel."
        )
    return api_key


def build_client() -> genai.Client:
    """
    Build and return an authenticated Gemini client.

    Returns:
        genai.Client
    """
    return genai.Client(api_key=get_api_key())


def _is_retryable(exc: Exception) -> bool:
    """
    Return True for transient errors that warrant trying the next model.

    Retryable: 503 Service Unavailable, 429 Resource Exhausted.

    Args:
        exc: Exception from the Gemini SDK.

    Returns:
        bool
    """
    if isinstance(exc, (genai_errors.ServerError, genai_errors.ClientError)):
        return getattr(exc, "status_code", None) in (429, 503)
    msg = str(exc)
    return "503" in msg or "429" in msg or "RESOURCE_EXHAUSTED" in msg


def _build_contents(
    history: list[dict],
    user_message: str,
    image_data: dict | None = None,
    pdf_context: str | None = None,
) -> list[types.Content]:
    """
    Construct the Gemini contents list from conversation history and the
    latest user turn (optionally including an image and/or PDF context).

    Args:
        history: Past turns — [{"role": "user"|"model", "parts": [...]}]
        user_message: Current user message text.
        image_data: Optional dict {"bytes": bytes, "mime_type": str}.
        pdf_context: Optional relevant text retrieved from an indexed PDF.

    Returns:
        list[types.Content]: Ready-to-send Gemini content list.
    """
    # Rebuild history as SDK Content objects
    contents = [
        types.Content(
            role=msg["role"],
            parts=[types.Part(text=part["text"]) for part in msg["parts"]],
        )
        for msg in history
    ]

    # Augment user message with PDF context if available
    if pdf_context:
        final_text = (
            "[Relevant context from uploaded document]\n"
            f"{pdf_context}\n\n"
            "Using the above context where relevant, answer the following:\n"
            f"{user_message}"
        )
    else:
        final_text = user_message

    # Build user parts — image first if present, then text
    if image_data:
        parts = [
            types.Part(
                inline_data=types.Blob(
                    mime_type=image_data["mime_type"],
                    data=image_data["bytes"],
                )
            ),
            types.Part(text=final_text),
        ]
    else:
        parts = [types.Part(text=final_text)]

    contents.append(types.Content(role="user", parts=parts))
    return contents


def send_message(
    history: list[dict],
    user_message: str,
    system_prompt: str | None = None,
    image_data: dict | None = None,
    pdf_context: str | None = None,
) -> str:
    """
    Send a message to Gemini with full conversation history and optional extras.

    Automatically falls back to the next model in _FALLBACK_MODELS if a
    503 (overloaded) or 429 (quota exceeded) error is encountered.

    Args:
        history: Past conversation turns.
        user_message: Current user text input.
        system_prompt: Optional system-level instruction (medical / research mode).
        image_data: Optional image dict {"bytes": bytes, "mime_type": str}.
        pdf_context: Optional document context string from FAISS search.

    Returns:
        str: Gemini's response text.

    Raises:
        RuntimeError: If all fallback models are exhausted.
    """
    client = build_client()
    contents = _build_contents(history, user_message, image_data, pdf_context)

    # Build config — conditionally include system_instruction
    config_kwargs: dict = {"max_output_tokens": 8192}
    if system_prompt:
        config_kwargs["system_instruction"] = system_prompt

    last_exc: Exception | None = None

    for model in _FALLBACK_MODELS:
        try:
            response = client.models.generate_content(
                model=model,
                contents=contents,
                config=types.GenerateContentConfig(**config_kwargs),
            )
            return response.text
        except Exception as exc:
            if _is_retryable(exc):
                last_exc = exc
                continue
            # Non-retryable (bad request, auth, etc.) — fail fast
            raise

    raise RuntimeError(
        f"All fallback models exhausted. Last error: {last_exc}"
    )
