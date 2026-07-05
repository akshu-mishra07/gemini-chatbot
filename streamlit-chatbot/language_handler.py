"""
language_handler.py - Automatic language detection and translation.

Detects the language of user input, translates it to English for Gemini,
and translates the response back to the original language.

Uses:
  - langdetect for language identification
  - deep-translator (GoogleTranslator) for reliable translation
"""

from langdetect import detect, LangDetectException
from deep_translator import GoogleTranslator

# Human-readable names for common language codes
LANGUAGE_NAMES: dict[str, str] = {
    "en": "English",
    "hi": "Hindi",
    "mr": "Marathi",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "zh-cn": "Chinese (Simplified)",
    "zh-tw": "Chinese (Traditional)",
    "ja": "Japanese",
    "ko": "Korean",
    "ar": "Arabic",
    "ru": "Russian",
    "bn": "Bengali",
    "ta": "Tamil",
    "te": "Telugu",
    "gu": "Gujarati",
    "ur": "Urdu",
}

# Minimum text length for reliable language detection
_MIN_DETECT_LENGTH = 5

# Max characters deep-translator handles per request
_MAX_TRANSLATE_CHARS = 4500


def detect_language(text: str) -> str:
    """
    Detect the language of the given text.

    Args:
        text: Input string from the user.

    Returns:
        str: ISO 639-1 language code (e.g. 'en', 'hi'). Falls back to 'en'.
    """
    if len(text.strip()) < _MIN_DETECT_LENGTH:
        return "en"
    try:
        return detect(text)
    except LangDetectException:
        return "en"


def translate_to_english(text: str, source_lang: str) -> str:
    """
    Translate text from source_lang to English.

    Args:
        text: Text to translate.
        source_lang: ISO 639-1 source language code.

    Returns:
        str: Translated English text, or original on failure.
    """
    if source_lang == "en":
        return text
    try:
        # Truncate to safe limit if necessary
        chunk = text[:_MAX_TRANSLATE_CHARS]
        return GoogleTranslator(source=source_lang, target="en").translate(chunk)
    except Exception:
        return text  # Graceful fallback — send original to Gemini


def translate_from_english(text: str, target_lang: str) -> str:
    """
    Translate English text back to the target language.

    Args:
        text: English text to translate.
        target_lang: ISO 639-1 target language code.

    Returns:
        str: Translated text, or original English on failure.
    """
    if target_lang == "en":
        return text
    try:
        # Translate in chunks if the text is long
        if len(text) <= _MAX_TRANSLATE_CHARS:
            return GoogleTranslator(source="en", target=target_lang).translate(text)
        # Chunk and rejoin for long responses
        parts = []
        for i in range(0, len(text), _MAX_TRANSLATE_CHARS):
            chunk = text[i: i + _MAX_TRANSLATE_CHARS]
            parts.append(
                GoogleTranslator(source="en", target=target_lang).translate(chunk)
            )
        return " ".join(parts)
    except Exception:
        return text  # Graceful fallback — return English response


def get_language_name(lang_code: str) -> str:
    """Return a human-readable language name for a language code."""
    return LANGUAGE_NAMES.get(lang_code, lang_code.upper())
