from __future__ import annotations

"""Language detection, translation, and response-language policy with Translation Memory."""

from typing import Any
import streamlit as st


SUPPORTED_LANGUAGES = {
    "auto": "Auto detect",
    "en": "English",
    "hi": "Hindi",
    "mr": "Marathi",
    "es": "Spanish",
}

VOICE_READY_CONFIG = {
    "input_format": "microphone_stream",
    "output_format": "tts_stream",
    "supported_languages": ["en", "hi", "mr", "es"],
    "provider_slot": "future_speech_adapter",
}


def detect_language(text: str) -> str:
    try:
        from langdetect import detect

        lang = detect(text)
        return lang if lang in SUPPORTED_LANGUAGES else "en"
    except Exception:
        return "en"


@st.cache_resource(show_spinner=False)
def _get_translator(source: str, target: str):
    from deep_translator import GoogleTranslator
    return GoogleTranslator(source=source, target=target)


@st.cache_data(show_spinner=False)
def translate_text(text: str, source: str, target: str) -> str:
    if not text or source == target:
        return text

    # 1. Query translation memory (SQLite)
    from database.storage import get_cached_translation, set_cached_translation
    cached = get_cached_translation(text, source, target)
    if cached:
        return cached

    # 2. Fall back to online translation service
    try:
        source_lang = "auto" if source == "auto" else source
        translator = _get_translator(source_lang, target)
        translated = translator.translate(text)
        
        # Cache the result persistently
        set_cached_translation(text, source, target, translated)
        return translated
    except Exception:
        return text


@st.cache_data(show_spinner=False)
def prepare_language_context(text: str, selected_language: str = "auto") -> dict[str, Any]:
    detected = detect_language(text)
    target = detected if selected_language == "auto" else selected_language
    if target not in SUPPORTED_LANGUAGES or target == "auto":
        target = "en"

    english_text = text if detected == "en" else translate_text(text, detected, "en")
    return {
        "detected_language": detected,
        "target_language": target,
        "english_text": english_text,
        "original_text": text,
        "translated": english_text != text,
    }


def build_language_instruction(language_context: dict[str, Any]) -> str:
    target = language_context.get("target_language", "en")
    detected = language_context.get("detected_language", "en")
    target_name = SUPPORTED_LANGUAGES.get(target, "English")
    detected_name = SUPPORTED_LANGUAGES.get(detected, "English")
    return (
        f"Detected user language: {detected_name}. "
        f"Respond in {target_name}. Preserve names, citations, numbers, code, and medical terminology accurately. "
        "If the user communicates using mixed languages (e.g. Hinglish, Spanglish) or code-switches naturally, you may adapt "
        "your response to use a similar blended language style or match their language mix. Ensure your response is culturally appropriate, "
        "courteous, and maintains the required safety rules."
    )


def build_model_user_message(language_context: dict[str, Any]) -> str:
    original = language_context.get("original_text", "")
    english_text = language_context.get("english_text", original)
    detected = SUPPORTED_LANGUAGES.get(language_context.get("detected_language", "en"), "English")
    if english_text == original:
        return original
    return (
        f"Original user message ({detected}): {original}\n\n"
        f"English translation for retrieval and reasoning: {english_text}"
    )
