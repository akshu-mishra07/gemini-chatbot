"""
chatbot.py - Gemini API integration module.

Handles all communication with Google's Gemini API using the latest
google.genai SDK. Automatically falls back through a priority list of
models when one returns a 503 (overloaded) or quota/rate-limit error.
"""

import os
from google import genai
from google.genai import types
from google.genai import errors as genai_errors

# Models tried in order. On 503 or quota failure the next one is used.
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
        str: The API key string.

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
    Build and return a configured Gemini client.

    Returns:
        genai.Client: An authenticated Gemini client.
    """
    return genai.Client(api_key=get_api_key())


def _is_retryable(exc: Exception) -> bool:
    """
    Return True if the error is a transient failure we should fall back on.

    Retryable conditions:
    - 503 Service Unavailable (model overloaded)
    - 429 Resource Exhausted (quota / rate limit exceeded)

    Args:
        exc: The exception raised by the Gemini SDK.

    Returns:
        bool: True if we should try the next model, False otherwise.
    """
    if isinstance(exc, (genai_errors.ServerError, genai_errors.ClientError)):
        code = getattr(exc, "status_code", None)
        return code in (429, 503)
    # Also catch by message as a safety net
    msg = str(exc)
    return "503" in msg or "429" in msg or "RESOURCE_EXHAUSTED" in msg


def _build_contents(history: list[dict], user_message: str) -> list[types.Content]:
    """
    Convert stored history dicts into SDK Content objects and append the
    latest user message.

    Args:
        history: Past messages — [{"role": "user"|"model", "parts": [...]}]
        user_message: The new message from the user.

    Returns:
        list[types.Content]: Ready-to-send contents list.
    """
    contents = [
        types.Content(
            role=msg["role"],
            parts=[types.Part(text=part["text"]) for part in msg["parts"]],
        )
        for msg in history
    ]
    contents.append(
        types.Content(role="user", parts=[types.Part(text=user_message)])
    )
    return contents


def send_message(history: list[dict], user_message: str) -> str:
    """
    Send a user message to Gemini with full conversation history.

    Tries each model in _FALLBACK_MODELS in order. If a model returns a
    503 (overloaded) or 429 (quota exceeded) error, the next model in the
    list is tried automatically. Raises the last error if all models fail.

    Args:
        history: Past messages — [{"role": "user"|"model", "parts": [...]}]
        user_message: The text typed by the user.

    Returns:
        str: The assistant's response text.

    Raises:
        RuntimeError: If all fallback models are exhausted.
    """
    client = build_client()
    contents = _build_contents(history, user_message)

    last_exc: Exception | None = None

    for model in _FALLBACK_MODELS:
        try:
            response = client.models.generate_content(
                model=model,
                contents=contents,
                config=types.GenerateContentConfig(max_output_tokens=8192),
            )
            return response.text
        except Exception as exc:
            if _is_retryable(exc):
                # Log which model failed and try the next one
                last_exc = exc
                continue
            # Non-retryable error (e.g. bad request, auth) — raise immediately
            raise

    raise RuntimeError(
        f"All fallback models exhausted. Last error: {last_exc}"
    )
