"""
chatbot.py - Gemini API integration module.

Handles all communication with Google's Gemini API using the latest
google.genai SDK. Automatically falls back through a priority list of
models when one returns a 503 (overloaded) or quota/rate-limit error.
"""

import os
import sys
import time
import random
from dotenv import load_dotenv
from google import genai
from google.genai import types
from google.genai import errors as genai_errors

# Load environment variables from .env file relative to this file's directory
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
load_dotenv(env_path)

# Models tried in order. On 503 or quota failure the next one is used.
_FALLBACK_MODELS = [
    "gemini-2.5-flash-lite",
    "gemini-2.5-flash",
    "gemini-2.0-flash",
]


class GeminiQuotaError(RuntimeError):
    """Exception raised when the Gemini API quota is exceeded or rate limited."""
    pass


def get_api_key() -> str:
    """
    Read the Gemini API key from session state or environment variables.

    Returns:
        str: The API key string.

    Raises:
        ValueError: If GEMINI_API_KEY is not set.
    """
    api_key = None
    try:
        import streamlit as st
        if "custom_api_key" in st.session_state and st.session_state.custom_api_key:
            api_key = st.session_state.custom_api_key
    except Exception:
        pass

    if not api_key:
        api_key = os.environ.get("GEMINI_API_KEY")

    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY environment variable is not set. "
            "Please configure a valid Gemini API key in the Settings panel."
        )
    
    # Task 3: Print first and last 4 characters of the loaded key
    masked_key = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) >= 8 else "Too Short"
    print(f"[Gemini Key Load Check] Loaded API key: {masked_key}", file=sys.stderr)
    return api_key


import streamlit as st

_cached_client = None

@st.cache_resource(show_spinner=False)
def _get_cached_client(api_key: str) -> genai.Client:
    return genai.Client(api_key=api_key)


def build_client() -> genai.Client:
    """
    Build and return a configured Gemini client.

    Returns:
        genai.Client: An authenticated Gemini client.
    """
    global _cached_client
    if _cached_client is not None:
        return _cached_client
    _cached_client = _get_cached_client(get_api_key())
    return _cached_client


def _is_quota_error(exc: Exception) -> bool:
    """
    Return True if the error is a quota / rate limit failure (429 or RESOURCE_EXHAUSTED).
    """
    code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
    if code == 429:
        return True
    msg = str(exc).lower()
    return "429" in msg or "resource_exhausted" in msg or "quota exceeded" in msg or "rate limit exceeded" in msg


def _is_hard_quota_exhausted(exc: Exception) -> bool:
    """
    Return True if the error indicates a hard daily quota exhaustion where retrying is useless.
    """
    msg = str(exc).lower()
    return "limit: 0" in msg or "daily limit" in msg or "daily quota" in msg


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
    code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
    if code in (429, 503):
        return True
    # Also catch by message as a safety net
    msg = str(exc)
    return "503" in msg or "429" in msg or "RESOURCE_EXHAUSTED" in msg


def _build_contents(history: list[dict], user_message: str, images: list = None) -> list[types.Content]:
    """
    Convert stored history dicts into SDK Content objects and append the
    latest user message along with optional images.

    Args:
        history: Past messages — [{"role": "user"|"model", "parts": [...]}]
        user_message: The new message from the user.
        images: Optional list of PIL.Image.Image objects.

    Returns:
        list[types.Content]: Ready-to-send contents list.
    """
    import io
    contents = []
    for msg in history:
        parts = []
        for part in msg["parts"]:
            if "text" in part:
                parts.append(types.Part(text=part["text"]))
            elif "inline_data" in part:
                parts.append(
                    types.Part.from_bytes(
                        data=part["inline_data"]["data"],
                        mime_type=part["inline_data"]["mime_type"]
                    )
                )
        contents.append(types.Content(role=msg["role"], parts=parts))
    
    parts = [types.Part(text=user_message)]
    
    # Process and append images as inline JPEG data parts
    if images:
        for img in images:
            img_byte_arr = io.BytesIO()
            # Convert to RGB to discard alpha channel if PNG has one (avoids JPEG conversion error)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img.save(img_byte_arr, format='JPEG')
            img_bytes = img_byte_arr.getvalue()
            parts.append(
                types.Part.from_bytes(
                    data=img_bytes,
                    mime_type="image/jpeg"
                )
            )

    contents.append(
        types.Content(role="user", parts=parts)
    )
    return contents


def get_retry_delay(exc: Exception) -> float:
    """
    Tries to parse the retry delay from the Gemini API exception details or message.
    Defaults to 15.0 seconds if not found or parsing fails.
    """
    try:
        if hasattr(exc, "details") and exc.details:
            for detail in exc.details:
                if isinstance(detail, dict) and "retryDelay" in detail:
                    delay_str = detail["retryDelay"]
                    if isinstance(delay_str, str) and delay_str.endswith("s"):
                        return float(delay_str[:-1])
                elif hasattr(detail, "retry_delay") and detail.retry_delay:
                    return detail.retry_delay.seconds + detail.retry_delay.nanos / 1e9
    except Exception:
        pass
    
    try:
        msg = str(exc)
        import re
        match = re.search(r"retry in (\d+(\.\d+)?)s", msg, re.IGNORECASE)
        if match:
            return float(match.group(1))
    except Exception:
        pass
        
    return 15.0


def test_api_connectivity(api_key: str | None = None) -> dict:
    """
    Performs a live connectivity test using the provided or loaded API key.
    Detects:
    - Missing key
    - Invalid key
    - Quota exceeded
    - Billing disabled
    - Rate limit exceeded
    - Offline / Generic Error
    
    Returns a dictionary of diagnostics:
    {
        "status": "Online" | "Offline" | "Quota Exceeded" | "Invalid Key" | "Billing Disabled" | "Rate Limit Exceeded" | "Missing Key",
        "error_message": str | None,
        "key_masked": str
    }
    """
    if not api_key:
        try:
            api_key = get_api_key()
        except Exception as e:
            return {
                "status": "Missing Key",
                "error_message": str(e),
                "key_masked": "Missing"
            }
            
    masked_key = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) >= 8 else "Too Short"
    
    print(f"[Gemini API Diagnostics] Running connectivity check on key: {masked_key}", file=sys.stderr)
    
    try:
        temp_client = genai.Client(api_key=api_key)
        # 1. Attempt to list models as a connectivity test
        list(temp_client.models.list())
        
        # 2. Attempt a lightweight content generation to test generation quota specifically
        temp_client.models.generate_content(
            model="gemini-2.5-flash-lite",
            contents="Say 'connectivity test successful'.",
        )
        return {
            "status": "Online",
            "error_message": None,
            "key_masked": masked_key
        }
    except Exception as exc:
        # Log exact Gemini exception to sys.stderr for Task 6
        print(f"[Gemini Connectivity Test Exception] Key: {masked_key} - Exception: {exc}", file=sys.stderr)
        
        msg = str(exc).lower()
        code = getattr(exc, "code", None) or getattr(exc, "status_code", None)
        
        # Check details or body for richer info if present
        details_str = ""
        if hasattr(exc, "details") and exc.details:
            details_str = str(exc.details).lower()
            
        status = "Offline"
        
        # Detect Quota Exceeded (specifically daily limit or generic quota limit)
        if any(t in msg for t in ["daily limit", "daily quota", "quota exceeded", "exceeded your current quota", "quota exceeded for metric", "freetier", "free_tier", "current quota"]):
            status = "Quota Exceeded"
        # Detect Billing Disabled
        elif any(t in msg for t in ["billing is not enabled", "billingdisabled", "billing_disabled", "billing is disabled"]) or "billingnotenabled" in msg:
            status = "Billing Disabled"
        # Detect Rate Limit Exceeded
        elif any(t in msg for t in ["rate limit", "429", "resource_exhausted", "too many requests"]) or code == 429:
            status = "Rate Limit Exceeded"
        # Detect Invalid Key
        elif any(t in msg for t in ["invalid key", "key not valid", "api key not valid", "invalid_argument", "bad request"]) or code == 400 or code == 403:
            status = "Invalid Key"
            
        return {
            "status": status,
            "error_message": str(exc),
            "key_masked": masked_key
        }


def validate_api_key(api_key: str) -> tuple[bool, str]:
    """
    Validates a Gemini API Key using the connectivity test.
    Returns (is_valid, message).
    """
    if not api_key or not api_key.strip():
        return False, "API Key cannot be empty."
    
    diag = test_api_connectivity(api_key)
    if diag["status"] == "Online":
        return True, "API key is valid and active!"
    elif diag["status"] == "Quota Exceeded":
        return False, "API Key is valid, but has no quota left. Please try again later."
    elif diag["status"] == "Rate Limit Exceeded":
        return False, "API Key is valid, but currently rate limited. Please try again later."
    elif diag["status"] == "Billing Disabled":
        return False, "Billing is disabled for this project/API key. Please enable billing in Google AI Studio."
    elif diag["status"] == "Invalid Key":
        return False, "Invalid API Key. Please verify your credentials."
    else:
        return False, f"Validation failed ({diag['status']}): {diag['error_message']}"


def send_message(
    history: list[dict],
    user_message: str,
    system_instruction: str | None = None,
    images: list = None,
    temperature: float = 1.0,
    max_output_tokens: int = 8192,
    top_p: float = 0.95
) -> str:
    """
    Send a user message to Gemini with full conversation history and optional images.

    Tries each model in _FALLBACK_MODELS in order. If a model returns a
    503 (overloaded) or 429 (quota exceeded) error, the next model in the
    list is tried automatically. Raises the last error if all models fail.
    """
    client = build_client()
    contents = _build_contents(history, user_message, images)

    import datetime
    current_date = datetime.datetime.now().strftime("%A, %B %d, %Y")
    current_time = datetime.datetime.now().strftime("%I:%M %p")
    time_prefix = f"[System Context: Current Date: {current_date}. Current Time: {current_time}.]"

    config = types.GenerateContentConfig(
        max_output_tokens=max_output_tokens,
        temperature=temperature,
        top_p=top_p
    )
    if system_instruction:
        config.system_instruction = f"{time_prefix}\n\n{system_instruction}"
    else:
        config.system_instruction = time_prefix

    last_exc: Exception | None = None

    for model in _FALLBACK_MODELS:
        # Cache active model in session state to show current model used
        try:
            import streamlit as st
            st.session_state.active_model_used = model
        except Exception:
            pass

        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=config,
                )
                return response.text
            except Exception as exc:
                # Log detailed error to terminal console
                print(f"[Gemini API Error] Model: {model}, Attempt: {attempt+1}/3 - {exc}", file=sys.stderr)
                last_exc = exc
                
                # Check for quota/rate limit: Requirement 7 requires skipping model on quota/rate-limit error
                if _is_quota_error(exc):
                    print(f"[Gemini Quota] Quota/Rate-limit error on model {model}. Skipping and trying next fallback model.", file=sys.stderr)
                    break
                
                # Exponential backoff for other retryable errors (e.g. 503)
                if _is_retryable(exc):
                    base_delay = 1.0 * (2.0 ** attempt)
                    jitter = random.uniform(0.0, 0.5)
                    sleep_time = base_delay + jitter
                    print(f"Transient error on model {model} (attempt {attempt+1}/3). Sleeping {sleep_time:.2f}s...", file=sys.stderr)
                    time.sleep(sleep_time)
                    continue
                raise exc

    if last_exc and _is_quota_error(last_exc):
        raise GeminiQuotaError(
            "AI service is temporarily unavailable. Please check your Gemini API key, billing, or quota."
        ) from last_exc

    raise RuntimeError(
        f"AI service is temporarily unavailable. Please check your Gemini API key, billing, or quota."
    )


def send_message_stream(
    history: list[dict],
    user_message: str,
    system_instruction: str | None = None,
    images: list = None,
    temperature: float = 1.0,
    max_output_tokens: int = 8192,
    top_p: float = 0.95
):
    """
    Send a user message to Gemini and yield chunks of response text in real-time.

    Tries each model in _FALLBACK_MODELS in order. Uses the same fallback
    and error checking logic as send_message, but streams the response.
    """
    client = build_client()
    contents = _build_contents(history, user_message, images)

    import datetime
    current_date = datetime.datetime.now().strftime("%A, %B %d, %Y")
    current_time = datetime.datetime.now().strftime("%I:%M %p")
    time_prefix = f"[System Context: Current Date: {current_date}. Current Time: {current_time}.]"

    config = types.GenerateContentConfig(
        max_output_tokens=max_output_tokens,
        temperature=temperature,
        top_p=top_p
    )
    if system_instruction:
        config.system_instruction = f"{time_prefix}\n\n{system_instruction}"
    else:
        config.system_instruction = time_prefix

    last_exc: Exception | None = None

    for model in _FALLBACK_MODELS:
        # Cache active model in session state to show current model used
        try:
            import streamlit as st
            st.session_state.active_model_used = model
        except Exception:
            pass

        for attempt in range(3):
            try:
                response_stream = client.models.generate_content_stream(
                    model=model,
                    contents=contents,
                    config=config,
                )
                
                # Retrieve the first chunk to verify the model call succeeds
                iterator = iter(response_stream)
                try:
                    first_chunk = next(iterator)
                except StopIteration:
                    return

                if first_chunk.text:
                    yield first_chunk.text

                for chunk in iterator:
                    if chunk.text:
                        yield chunk.text
                return
            except Exception as exc:
                # Log detailed error to terminal console
                print(f"[Gemini Stream Error] Model: {model}, Attempt: {attempt+1}/3 - {exc}", file=sys.stderr)
                last_exc = exc
                
                # Check for quota/rate limit: Requirement 7 requires skipping model on quota/rate-limit error
                if _is_quota_error(exc):
                    print(f"[Gemini Quota] Quota/Rate-limit error on stream model {model}. Skipping and trying next fallback model.", file=sys.stderr)
                    break
                
                # Exponential backoff for other retryable errors (e.g. 503)
                if _is_retryable(exc):
                    base_delay = 1.0 * (2.0 ** attempt)
                    jitter = random.uniform(0.0, 0.5)
                    sleep_time = base_delay + jitter
                    print(f"Transient error on stream model {model} (attempt {attempt+1}/3). Sleeping {sleep_time:.2f}s...", file=sys.stderr)
                    time.sleep(sleep_time)
                    continue
                raise exc

    if last_exc and _is_quota_error(last_exc):
        raise GeminiQuotaError(
            "AI service is temporarily unavailable. Please check your Gemini API key, billing, or quota."
        ) from last_exc

    raise RuntimeError(
        f"AI service is temporarily unavailable. Please check your Gemini API key, billing, or quota."
    )
