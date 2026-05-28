"""
app.py - Advanced AI Assistant entry point.

Modes:
  - General Chat        : Standard Gemini conversation with full history
  - Medical Assistant   : Safe health information with mandatory disclaimers
  - Research Assistant  : Academic/document analysis & summarisation

Cross-cutting features (all modes):
  - PDF upload  → TF-IDF + FAISS semantic search (offline, no API dependency)
  - Image upload → Gemini Vision analysis
  - Real-time date/time context (always accurate)
  - Sentiment-aware response tone (TextBlob)
  - Auto language detection & translation (Hindi, Marathi, 20+ languages)
"""

import streamlit as st

# Core chatbot
from chatbot import send_message, build_client

# Feature modules
from datetime_handler import build_datetime_context
from sentiment_handler import analyze_sentiment, get_tone_instruction, get_sentiment_emoji
from language_handler import (
    detect_language,
    translate_to_english,
    translate_from_english,
    get_language_name,
)
from medical_bot import get_system_prompt, add_medical_disclaimer
from image_handler import process_image, analyze_image
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
# Dark gradient theme + badge styles
# ============================================================================
st.markdown(
    """
    <style>
    /* Dark gradient background */
    .stApp {
        background: linear-gradient(135deg, #0f0f1a 0%, #1a1a2e 40%, #16213e 100%);
        color: #e0e0e0;
    }
    /* Sidebar dark */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #12122a 0%, #1e1e3a 100%);
    }
    /* Chat message bubbles */
    [data-testid="stChatMessage"] {
        background: rgba(255,255,255,0.04);
        border-radius: 12px;
        border: 1px solid rgba(255,255,255,0.07);
        margin-bottom: 8px;
    }
    /* Input box */
    [data-testid="stChatInput"] textarea {
        background: rgba(255,255,255,0.06) !important;
        border: 1px solid rgba(100,120,200,0.4) !important;
        color: #e0e0e0 !important;
        border-radius: 12px !important;
    }
    /* Buttons */
    .stButton > button {
        background: linear-gradient(90deg, #4a4af0 0%, #7b2ff7 100%);
        color: white;
        border: none;
        border-radius: 8px;
    }
    .stButton > button:hover {
        background: linear-gradient(90deg, #6a6af8 0%, #9b4ffa 100%);
    }
    /* PDF context active badge */
    .pdf-badge {
        display: inline-block;
        background: linear-gradient(90deg, #00c853, #00e676);
        color: #000;
        font-weight: 700;
        font-size: 0.72rem;
        padding: 3px 10px;
        border-radius: 20px;
        letter-spacing: 0.04em;
        margin-left: 8px;
        vertical-align: middle;
    }
    /* Mode badge */
    .mode-badge {
        display: inline-block;
        background: linear-gradient(90deg, #4a4af0, #7b2ff7);
        color: white;
        font-size: 0.72rem;
        padding: 3px 10px;
        border-radius: 20px;
        margin-left: 8px;
        vertical-align: middle;
    }
    /* Section headers */
    h1, h2, h3 { color: #c8c8ff; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================================
# Session state defaults
# ============================================================================
_DEFAULTS: dict = {
    # Chat history
    "messages": [],           # Display history
    "gemini_history": [],     # Gemini SDK format

    # Assistant mode
    "mode": "general",        # "general" | "medical" | "research"

    # PDF state — TF-IDF + FAISS (no Gemini embedding API)
    "pdf_index": None,        # faiss.Index
    "pdf_chunks": None,       # list[str] parallel to index
    "pdf_vectorizer": None,   # fitted TfidfVectorizer
    "pdf_svd": None,          # fitted TruncatedSVD
    "pdf_name": None,         # uploaded filename
    "pdf_chunk_count": 0,     # number of indexed chunks

    # Image state
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
    st.markdown("## 🤖 AI Assistant")
    st.markdown("---")

    # ── Mode selector ────────────────────────────────────────────────────────
    st.markdown("### 🧠 Mode")
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
    st.markdown("### 📄 Document (PDF)")
    uploaded_pdf = st.file_uploader(
        "Upload PDF",
        type=["pdf"],
        label_visibility="collapsed",
    )

    if uploaded_pdf is not None and uploaded_pdf.name != st.session_state.pdf_name:
        with st.spinner(f"Indexing **{uploaded_pdf.name}** (TF-IDF + FAISS)…"):
            try:
                index, chunks, vectorizer, svd, _ = process_pdf(uploaded_pdf.read())
                st.session_state.pdf_index = index
                st.session_state.pdf_chunks = chunks
                st.session_state.pdf_vectorizer = vectorizer
                st.session_state.pdf_svd = svd
                st.session_state.pdf_name = uploaded_pdf.name
                st.session_state.pdf_chunk_count = len(chunks)
                st.success(f"✅ Indexed — {len(chunks)} chunks ready for Q&A")
            except Exception as e:
                st.error(f"PDF processing failed: {e}")

    if st.session_state.pdf_name:
        st.info(
            f"📎 **{st.session_state.pdf_name}**  \n"
            f"{st.session_state.pdf_chunk_count} chunks · FAISS indexed"
        )
        if st.button("🗑️ Remove PDF", use_container_width=True):
            for _key in ("pdf_index", "pdf_chunks", "pdf_vectorizer",
                         "pdf_svd", "pdf_name"):
                st.session_state[_key] = None
            st.session_state.pdf_chunk_count = 0
            st.rerun()

    st.markdown("---")

    # ── Image upload ─────────────────────────────────────────────────────────
    st.markdown("### 🖼️ Image Analysis")
    uploaded_image = st.file_uploader(
        "Upload image",
        type=["jpg", "jpeg", "png", "webp"],
        label_visibility="collapsed",
    )

    if uploaded_image is not None and uploaded_image.name != st.session_state.image_name:
        with st.spinner("Processing image…"):
            try:
                proc_bytes, mime = process_image(uploaded_image.read())
                st.session_state.image_bytes = proc_bytes
                st.session_state.image_mime = mime
                st.session_state.image_name = uploaded_image.name
                st.success("✅ Image ready — ask a question about it")
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
    st.markdown("### 🌍 Language")
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
    st.markdown("### 💬 Chat")
    if st.button("🗑️ Clear conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.gemini_history = []
        st.session_state.detected_lang = "en"
        st.rerun()

# ============================================================================
# Main header with active context badges
# ============================================================================
_MODE_EMOJI = {"general": "💬", "medical": "🏥", "research": "📚"}

_badges = ""
if st.session_state.pdf_name:
    _badges += '<span class="pdf-badge">📎 PDF Context Active</span>'
if st.session_state.mode != "general":
    _badges += f'<span class="mode-badge">{selected_label}</span>'

st.markdown(
    f"<h1>{_MODE_EMOJI[st.session_state.mode]} Advanced AI Assistant{_badges}</h1>",
    unsafe_allow_html=True,
)

# Sub-status line
_status_parts = []
if st.session_state.pdf_name:
    _status_parts.append(f"📎 {st.session_state.pdf_name} ({st.session_state.pdf_chunk_count} chunks)")
if st.session_state.image_name:
    _status_parts.append(f"🖼️ {st.session_state.image_name}")
if st.session_state.auto_translate:
    _status_parts.append(f"🌍 {get_language_name(st.session_state.detected_lang)}")

if _status_parts:
    st.caption(" · ".join(_status_parts))

st.markdown("---")

# ── Display existing chat history ────────────────────────────────────────────
for _msg in st.session_state.messages:
    with st.chat_message(_msg["role"]):
        st.markdown(_msg["content"])

# ============================================================================
# Chat input & full message pipeline
# ============================================================================
user_input = st.chat_input("Ask me anything…")

if user_input:

    # ── Step 1: Language detection & translation ─────────────────────────────
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

    # ── Step 2: Display user message ─────────────────────────────────────────
    with st.chat_message("user"):
        st.markdown(user_input)
        if original_lang != "en":
            st.caption(
                f"🌍 {get_language_name(original_lang)} detected — "
                "translating to English for Gemini"
            )

    # Persist: original for display, English for Gemini history
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

    mode_prompt = get_system_prompt(st.session_state.mode)
    if mode_prompt:
        _system_parts.append(mode_prompt)

    _system_parts.append(get_tone_instruction(sentiment["label"]))
    _system_parts.append(build_datetime_context())   # always inject accurate datetime

    system_prompt = "\n\n".join(_system_parts)

    # ── Step 5: PDF context retrieval via TF-IDF + FAISS ─────────────────────
    pdf_context: str | None = None
    if (
        st.session_state.pdf_index is not None
        and st.session_state.pdf_chunks
        and st.session_state.pdf_vectorizer is not None
        and st.session_state.pdf_svd is not None
    ):
        try:
            pdf_context = search_context(
                query=english_input,
                index=st.session_state.pdf_index,
                chunks=st.session_state.pdf_chunks,
                vectorizer=st.session_state.pdf_vectorizer,
                svd=st.session_state.pdf_svd,
                k=4,
            )
        except Exception:
            pdf_context = None

    # ── Step 6: Image data ───────────────────────────────────────────────────
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
                    client = build_client()
                    english_reply = analyze_image(
                        client=client,
                        image_bytes=image_data["bytes"],
                        mime_type=image_data["mime_type"],
                        user_prompt=english_input,
                    )
                else:
                    # Text chat — may include PDF context injection
                    english_reply = send_message(
                        history=st.session_state.gemini_history[:-1],
                        user_message=english_input,
                        system_prompt=system_prompt,
                        image_data=None,
                        pdf_context=pdf_context,
                    )

                # ── Step 8: Post-process ──────────────────────────────────────
                reply = english_reply

                if st.session_state.mode == "medical":
                    reply = add_medical_disclaimer(reply)

                if original_lang != "en" and st.session_state.auto_translate:
                    try:
                        reply = translate_from_english(reply, original_lang)
                    except Exception:
                        pass  # Graceful fallback — show English response

                # ── Step 9: Display ───────────────────────────────────────────
                st.markdown(reply)

                # Collapsible metadata panel
                with st.expander("ℹ️ Message details", expanded=False):
                    col1, col2 = st.columns(2)
                    with col1:
                        emoji = get_sentiment_emoji(sentiment["label"])
                        st.write(
                            f"**Sentiment:** {emoji} "
                            f"{sentiment['label'].capitalize()} "
                            f"(polarity: {sentiment['polarity']})"
                        )
                        st.write(
                            f"**Language:** {get_language_name(original_lang)} "
                            f"({original_lang})"
                        )
                    with col2:
                        st.write(f"**PDF context used:** {'✅' if pdf_context else '❌'}")
                        st.write(f"**Image included:** {'✅' if image_data else '❌'}")
                        st.write(f"**Mode:** {selected_label}")

                # ── Step 10: Persist ──────────────────────────────────────────
                st.session_state.messages.append(
                    {"role": "assistant", "content": reply}
                )
                st.session_state.gemini_history.append(
                    {"role": "model", "parts": [{"text": english_reply}]}
                )

            except ValueError as e:
                st.error(f"⚠️ Configuration error: {e}")
            except Exception as e:
                st.error(f"❌ {e}")
