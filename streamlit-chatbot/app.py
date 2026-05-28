"""
app.py - Advanced AI Assistant entry point.

Integrates all modules into one unified Streamlit chatbot:
  - General Chat        : Standard Gemini conversation with full history
  - Medical Assistant   : Safe health information with mandatory disclaimers
  - Research Assistant  : Academic/document analysis mode

Cross-cutting features (available in all modes):
  - PDF upload  → Gemini-powered semantic search (no local ML model)
  - Image upload → Gemini Vision analysis
  - Real-time date/time context (always accurate)
  - Sentiment-aware response tone (TextBlob)
  - Automatic language detection & translation (Hindi, Marathi, 20+ languages)
"""

import streamlit as st

# Core chatbot
from chatbot import send_message, build_client

# Feature modules
from datetime_handler import build_datetime_context, is_datetime_query
from sentiment_handler import analyze_sentiment, get_tone_instruction, get_sentiment_emoji
from language_handler import (
    detect_language,
    translate_to_english,
    translate_from_english,
    get_language_name,
)
from medical_bot import get_system_prompt, add_medical_disclaimer
from image_handler import process_image, analyze_image, get_mime_type
from pdf_handler import process_pdf, search_context

# ============================================================================
# Page configuration
# ============================================================================
st.set_page_config(
    page_title="Advanced AI Assistant",
    page_icon="🤖",
    layout="wide",
)

# ============================================================================
# Session state defaults
# ============================================================================
_DEFAULTS: dict = {
    # Chat history
    "messages": [],           # Display: [{"role": "user"|"assistant", "content": "..."}]
    "gemini_history": [],     # SDK format: [{"role": "user"|"model", "parts": [...]}]

    # Assistant mode
    "mode": "general",        # "general" | "medical" | "research"

    # PDF state (embeddings stored as numpy arrays — no FAISS needed)
    "pdf_embeddings": None,   # numpy array of shape (n_chunks, 768)
    "pdf_chunks": None,       # list[str] parallel to embeddings
    "pdf_name": None,         # uploaded filename
    "pdf_chunk_count": 0,     # number of indexed chunks

    # Image state (persists until user clears it)
    "image_bytes": None,
    "image_mime": None,
    "image_name": None,

    # Language
    "auto_translate": True,
    "detected_lang": "en",
}
for _k, _v in _DEFAULTS.items():
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ============================================================================
# Sidebar
# ============================================================================
with st.sidebar:
    st.title("🤖 AI Assistant")
    st.markdown("---")

    # ── Mode selector ────────────────────────────────────────────────────────
    st.subheader("🧠 Assistant Mode")
    _MODE_MAP = {
        "💬 General Chat": "general",
        "🏥 Medical Assistant": "medical",
        "📚 Research Assistant": "research",
    }
    _MODE_DESC = {
        "general": "Standard AI chat — ask me anything.",
        "medical": "Safe health information with professional disclaimers.",
        "research": "Academic analysis, document summarisation, technical Q&A.",
    }

    selected_label = st.selectbox(
        "Select mode",
        list(_MODE_MAP.keys()),
        index=list(_MODE_MAP.values()).index(st.session_state.mode),
        label_visibility="collapsed",
    )
    st.session_state.mode = _MODE_MAP[selected_label]
    st.caption(_MODE_DESC[st.session_state.mode])
    st.markdown("---")

    # ── PDF / Document upload ────────────────────────────────────────────────
    st.subheader("📄 Document (PDF)")
    uploaded_pdf = st.file_uploader(
        "Upload a PDF to enable semantic Q&A",
        type=["pdf"],
        label_visibility="collapsed",
    )

    if uploaded_pdf is not None and uploaded_pdf.name != st.session_state.pdf_name:
        with st.spinner(f"Indexing **{uploaded_pdf.name}** via Gemini…"):
            try:
                client = build_client()
                embeddings, chunks, _ = process_pdf(uploaded_pdf.read(), client)
                st.session_state.pdf_embeddings = embeddings
                st.session_state.pdf_chunks = chunks
                st.session_state.pdf_name = uploaded_pdf.name
                st.session_state.pdf_chunk_count = len(chunks)
                st.success(f"✅ Indexed — {len(chunks)} chunks ready")
            except Exception as e:
                st.error(f"PDF processing failed: {e}")

    if st.session_state.pdf_name:
        st.info(
            f"📎 **{st.session_state.pdf_name}**\n\n"
            f"{st.session_state.pdf_chunk_count} chunks indexed"
        )
        if st.button("🗑️ Remove PDF", use_container_width=True):
            st.session_state.pdf_embeddings = None
            st.session_state.pdf_chunks = None
            st.session_state.pdf_name = None
            st.session_state.pdf_chunk_count = 0
            st.rerun()

    st.markdown("---")

    # ── Image upload ─────────────────────────────────────────────────────────
    st.subheader("🖼️ Image Analysis")
    uploaded_image = st.file_uploader(
        "Upload an image for Gemini Vision",
        type=["jpg", "jpeg", "png", "webp"],
        label_visibility="collapsed",
    )

    if uploaded_image is not None and uploaded_image.name != st.session_state.image_name:
        with st.spinner("Processing image…"):
            try:
                raw_bytes = uploaded_image.read()
                proc_bytes, mime = process_image(raw_bytes)
                st.session_state.image_bytes = proc_bytes
                st.session_state.image_mime = mime
                st.session_state.image_name = uploaded_image.name
            except Exception as e:
                st.error(f"Image processing failed: {e}")

    if st.session_state.image_bytes:
        st.image(
            st.session_state.image_bytes,
            caption=st.session_state.image_name,
            use_container_width=True,
        )
        if st.button("🗑️ Remove Image", use_container_width=True):
            st.session_state.image_bytes = None
            st.session_state.image_mime = None
            st.session_state.image_name = None
            st.rerun()

    st.markdown("---")

    # ── Language settings ────────────────────────────────────────────────────
    st.subheader("🌍 Language")
    st.session_state.auto_translate = st.toggle(
        "Auto-detect & translate",
        value=st.session_state.auto_translate,
    )
    if st.session_state.auto_translate:
        lang_name = get_language_name(st.session_state.detected_lang)
        st.caption(f"Detected: **{lang_name}** ({st.session_state.detected_lang})")
    else:
        st.caption("Disabled — English responses only.")

    st.markdown("---")

    # ── Chat controls ────────────────────────────────────────────────────────
    st.subheader("💬 Chat")
    if st.button("🗑️ Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.gemini_history = []
        st.session_state.detected_lang = "en"
        st.rerun()

# ============================================================================
# Main chat area header
# ============================================================================
_MODE_EMOJI = {"general": "💬", "medical": "🏥", "research": "📚"}
st.title(f"{_MODE_EMOJI[st.session_state.mode]} Advanced AI Assistant")

# Active context status bar
_status_parts = []
if st.session_state.pdf_name:
    _status_parts.append(f"📎 PDF: {st.session_state.pdf_name}")
if st.session_state.image_name:
    _status_parts.append(f"🖼️ Image: {st.session_state.image_name}")
if st.session_state.mode != "general":
    _status_parts.append(f"Mode: {selected_label}")

if _status_parts:
    st.caption(" · ".join(_status_parts))

st.markdown("---")

# ── Display existing chat history ────────────────────────────────────────────
for _msg in st.session_state.messages:
    with st.chat_message(_msg["role"]):
        st.markdown(_msg["content"])

# ============================================================================
# Chat input & full pipeline
# ============================================================================
user_input = st.chat_input("Ask me anything…")

if user_input:

    # ── Step 1: Language detection & translation to English ──────────────────
    original_lang = "en"
    english_input = user_input

    if st.session_state.auto_translate:
        try:
            original_lang = detect_language(user_input)
            st.session_state.detected_lang = original_lang
            if original_lang != "en":
                english_input = translate_to_english(user_input, original_lang)
        except Exception:
            original_lang = "en"
            english_input = user_input

    # ── Step 2: Show user message immediately ────────────────────────────────
    with st.chat_message("user"):
        st.markdown(user_input)
        if original_lang != "en":
            st.caption(
                f"🌍 {get_language_name(original_lang)} detected — "
                "translating to English for Gemini…"
            )

    # Persist original message for display; English version for Gemini
    st.session_state.messages.append({"role": "user", "content": user_input})
    st.session_state.gemini_history.append(
        {"role": "user", "parts": [{"text": english_input}]}
    )

    # ── Step 3: Sentiment analysis ───────────────────────────────────────────
    try:
        sentiment = analyze_sentiment(english_input)
    except Exception:
        sentiment = {"label": "neutral", "polarity": 0.0, "subjectivity": 0.0}

    # ── Step 4: Build system prompt ──────────────────────────────────────────
    _system_parts: list[str] = []

    # Mode-specific system instruction
    mode_prompt = get_system_prompt(st.session_state.mode)
    if mode_prompt:
        _system_parts.append(mode_prompt)

    # Sentiment-based tone instruction
    _system_parts.append(get_tone_instruction(sentiment["label"]))

    # Real-time date/time — always inject so Gemini gives accurate answers
    _system_parts.append(build_datetime_context())

    system_prompt = "\n\n".join(_system_parts)

    # ── Step 5: PDF semantic context retrieval ───────────────────────────────
    pdf_context: str | None = None
    if st.session_state.pdf_embeddings is not None and st.session_state.pdf_chunks:
        try:
            client = build_client()
            pdf_context = search_context(
                query=english_input,
                client=client,
                embeddings=st.session_state.pdf_embeddings,
                chunks=st.session_state.pdf_chunks,
                k=4,
            )
        except Exception:
            pdf_context = None

    # ── Step 6: Image data preparation ──────────────────────────────────────
    image_data: dict | None = None
    if st.session_state.image_bytes:
        image_data = {
            "bytes": st.session_state.image_bytes,
            "mime_type": st.session_state.image_mime,
        }

    # ── Step 7: Call Gemini ──────────────────────────────────────────────────
    with st.chat_message("assistant"):
        with st.spinner("Thinking…"):
            try:
                if image_data:
                    # Multimodal: use dedicated image analysis path
                    client = build_client()
                    english_reply = analyze_image(
                        client=client,
                        image_bytes=image_data["bytes"],
                        mime_type=image_data["mime_type"],
                        user_prompt=english_input,
                    )
                else:
                    # Text-only (may include PDF context)
                    # Pass history *excluding* the current turn (already appended above)
                    english_reply = send_message(
                        history=st.session_state.gemini_history[:-1],
                        user_message=english_input,
                        system_prompt=system_prompt,
                        image_data=None,
                        pdf_context=pdf_context,
                    )

                # ── Step 8: Post-process ─────────────────────────────────────
                reply = english_reply

                # Mandatory medical disclaimer in medical mode
                if st.session_state.mode == "medical":
                    reply = add_medical_disclaimer(reply)

                # Translate response back to user's original language
                if original_lang != "en" and st.session_state.auto_translate:
                    try:
                        reply = translate_from_english(reply, original_lang)
                    except Exception:
                        pass  # Fall back to English response

                # ── Step 9: Display ──────────────────────────────────────────
                st.markdown(reply)

                # Collapsible metadata panel
                with st.expander("ℹ️ Message details", expanded=False):
                    col1, col2 = st.columns(2)
                    with col1:
                        sentiment_emoji = get_sentiment_emoji(sentiment["label"])
                        st.write(
                            f"**Sentiment:** {sentiment_emoji} "
                            f"{sentiment['label'].capitalize()} "
                            f"(polarity: {sentiment['polarity']})"
                        )
                        st.write(
                            f"**Language:** {get_language_name(original_lang)} "
                            f"({original_lang})"
                        )
                    with col2:
                        st.write(
                            f"**PDF context:** {'✅ Yes' if pdf_context else '❌ No'}"
                        )
                        st.write(
                            f"**Image:** {'✅ Included' if image_data else '❌ None'}"
                        )
                        st.write(f"**Mode:** {selected_label}")

                # ── Step 10: Persist to session state ────────────────────────
                st.session_state.messages.append(
                    {"role": "assistant", "content": reply}
                )
                # Store English version in Gemini history for coherent follow-ups
                st.session_state.gemini_history.append(
                    {"role": "model", "parts": [{"text": english_reply}]}
                )

            except ValueError as e:
                st.error(f"⚠️ Configuration error: {e}")
            except Exception as e:
                st.error(f"❌ An error occurred: {e}")
