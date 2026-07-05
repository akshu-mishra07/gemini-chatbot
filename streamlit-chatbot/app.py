"""
app.py - Advanced AI Assistant entry point.

Implements a premium dark purple AI SaaS interface with 4 isolated modes:
  1. General Assistant - General AI chat with Gemini
  2. Knowledge Base Assistant - RAG over uploaded documents
  3. Medical Assistant - MedQuAD + Medical FAISS retrieval
  4. Image Analysis - Image upload and understanding

All modes are fully isolated: switching clears state, no shared banners/pipelines.
"""

import streamlit as st
import datetime
import os
import re
import random
import sys
import io
from pathlib import Path

# ---------------------------------------------------------------------------
# Page configuration (must be first Streamlit call)
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="OmniChat AI",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Premium CSS injection
# ---------------------------------------------------------------------------
PREMIUM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Outfit:wght@400;500;600;700;800&display=swap');

/* Root variables */
:root {
    --bg-primary: #0f0a1a;
    --bg-secondary: #160e29;
    --bg-card: rgba(30, 20, 60, 0.45);
    --accent-primary: #a78bfa;
    --accent-secondary: #7c3aed;
    --accent-glow: rgba(124, 58, 237, 0.35);
    --text-primary: #f8fafc;
    --text-secondary: #cbd5e1;
    --text-muted: #64748b;
    --border-color: rgba(167, 139, 250, 0.18);
    --success: #10b981;
    --warning: #f59e0b;
    --danger: #ef4444;
    --info: #0ea5e9;
}

/* Global overrides */
.stApp {
    background: linear-gradient(135deg, var(--bg-primary) 0%, var(--bg-secondary) 50%, #0d0520 100%) !important;
    font-family: 'Inter', sans-serif !important;
}

/* Header Redesign */
.omnichat-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: rgba(25, 15, 45, 0.55);
    border: 1px solid var(--border-color);
    border-radius: 16px;
    padding: 1.25rem 2rem;
    margin-bottom: 2rem;
    backdrop-filter: blur(12px);
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
}

.header-left h1 {
    font-family: 'Outfit', sans-serif !important;
    font-size: 1.75rem;
    font-weight: 800;
    margin: 0;
    background: linear-gradient(135deg, #c084fc, #a78bfa, #818cf8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.header-left p {
    color: var(--text-secondary);
    margin: 0.15rem 0 0 0;
    font-size: 0.8rem;
    font-weight: 500;
}

.header-right {
    display: flex;
    align-items: center;
    gap: 1.25rem;
}

.header-metric {
    display: flex;
    flex-direction: column;
    background: rgba(15, 10, 30, 0.6);
    border: 1px solid rgba(167, 139, 250, 0.12);
    padding: 0.3rem 0.75rem;
    border-radius: 8px;
}

.metric-label {
    font-size: 0.65rem;
    color: var(--text-muted);
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.metric-value {
    font-size: 0.8rem;
    color: var(--text-primary);
    font-weight: 600;
}

.header-status {
    font-size: 0.8rem;
    color: var(--success);
    display: flex;
    align-items: center;
    gap: 0.4rem;
    font-weight: 600;
}

.status-dot {
    width: 8px;
    height: 8px;
    background-color: var(--success);
    border-radius: 50%;
    display: inline-block;
    box-shadow: 0 0 10px var(--success);
}

.header-actions {
    display: flex;
    align-items: center;
    gap: 0.75rem;
}

.header-btn {
    cursor: pointer;
    font-size: 1.1rem;
    padding: 0.3rem;
    border-radius: 50%;
    transition: all 0.2s ease;
}

.header-btn:hover {
    background: rgba(167, 139, 250, 0.15);
    transform: scale(1.1);
}

.header-avatar {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    background: linear-gradient(135deg, var(--accent-secondary), var(--accent-primary));
    color: white;
    font-weight: 700;
    font-size: 0.85rem;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 1px solid rgba(255, 255, 255, 0.25);
    box-shadow: 0 2px 8px var(--accent-glow);
}

/* Sidebar Redesign & Cards */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #160e2a 0%, #0d081b 100%) !important;
    border-right: 1px solid var(--border-color) !important;
    padding: 1.5rem 0.5rem !important;
}

section[data-testid="stSidebar"] h2 {
    font-family: 'Outfit', sans-serif !important;
    font-weight: 700 !important;
    color: var(--text-primary) !important;
    font-size: 1.25rem !important;
    margin-bottom: 1.5rem !important;
    text-align: center;
}

section[data-testid="stSidebar"] div[data-testid="stExpander"] {
    background: rgba(30, 20, 60, 0.3) !important;
    border: 1px solid rgba(167, 139, 250, 0.15) !important;
    border-radius: 12px !important;
    margin-bottom: 0.85rem !important;
    backdrop-filter: blur(8px) !important;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.15) !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
}

section[data-testid="stSidebar"] div[data-testid="stExpander"]:hover {
    border-color: rgba(167, 139, 250, 0.35) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 25px rgba(124, 58, 237, 0.2) !important;
}

/* Sidebar labels and selections */
section[data-testid="stSidebar"] label {
    font-size: 0.8rem !important;
    font-weight: 600 !important;
    color: var(--text-secondary) !important;
    margin-bottom: 4px !important;
}

/* Expanders globally */
.streamlit-expanderHeader {
    background: transparent !important;
    border: none !important;
    font-size: 0.9rem !important;
    font-weight: 600 !important;
    color: var(--text-primary) !important;
}

/* Button UI system */
.stButton > button, .stDownloadButton > button {
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    width: 100% !important;
    height: 40px !important;
    border-radius: 8px !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    margin-bottom: 0.5rem !important;
    transition: all 0.25s ease !important;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1) !important;
    cursor: pointer !important;
}

/* Button style categorization */
/* 1. Primary buttons */
.stButton > button, 
button[key*="btn_proceed_gen"],
button[key*="btn_rebuild"] {
    background: linear-gradient(135deg, var(--accent-secondary), var(--accent-primary)) !important;
    color: white !important;
    border: none !important;
    box-shadow: 0 4px 14px var(--accent-glow) !important;
}

.stButton > button:hover, 
button[key*="btn_proceed_gen"]:hover,
button[key*="btn_rebuild"]:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(124, 58, 237, 0.55) !important;
}

/* 2. Secondary buttons (glassmorphism style) */
button[key*="btn_new_session"], 
button[key*="btn_save_session"], 
button[key*="btn_rename_session"], 
button[key*="btn_test_api"], 
button[key*="btn_save_watch"], 
button[key*="btn_sync_watch"],
button[key*="btn_download_"],
button[key*="dl_png_"],
button[key*="dl_jpg_"],
button[key*="upscale_"],
button[key*="ref_"] {
    background: rgba(30, 20, 60, 0.5) !important;
    border: 1px solid var(--border-color) !important;
    color: var(--text-primary) !important;
    box-shadow: none !important;
}

button[key*="btn_new_session"]:hover,
button[key*="btn_save_session"]:hover,
button[key*="btn_rename_session"]:hover,
button[key*="btn_test_api"]:hover,
button[key*="btn_save_watch"]:hover,
button[key*="btn_sync_watch"]:hover,
button[key*="btn_download_"]:hover,
button[key*="dl_png_"]:hover,
button[key*="dl_jpg_"]:hover,
button[key*="upscale_"]:hover,
button[key*="ref_"]:hover {
    background: rgba(167, 139, 250, 0.15) !important;
    border-color: var(--accent-primary) !important;
    transform: translateY(-1px) !important;
}

/* 3. Danger buttons */
button[key*="clear"],
button[key*="btn_clear"],
button[key*="delete"],
button[key*="btn_delete_session"],
button[key*="del_"] {
    background: rgba(239, 68, 68, 0.15) !important;
    border: 1px solid rgba(239, 68, 68, 0.35) !important;
    color: #fca5a5 !important;
    box-shadow: none !important;
}

button[key*="clear"]:hover,
button[key*="btn_clear"]:hover,
button[key*="delete"]:hover,
button[key*="btn_delete_session"]:hover,
button[key*="del_"]:hover {
    background: rgba(239, 68, 68, 0.3) !important;
    border-color: var(--danger) !important;
    transform: translateY(-1px) !important;
}

/* 4. Success / Actions */
button[key*="index"],
button[key*="btn_index"],
button[key*="btn_build_med"] {
    background: rgba(16, 185, 129, 0.15) !important;
    border: 1px solid rgba(16, 185, 129, 0.35) !important;
    color: #a7f3d0 !important;
    box-shadow: none !important;
}

button[key*="index"]:hover,
button[key*="btn_index"]:hover,
button[key*="btn_build_med"]:hover {
    background: rgba(16, 185, 129, 0.3) !important;
    border-color: var(--success) !important;
    transform: translateY(-1px) !important;
}

/* Input Fields & Text Areas */
.stSelectbox > div > div, 
.stTextInput > div > div, 
.stTextArea textarea {
    background: rgba(20, 10, 40, 0.6) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 8px !important;
    color: var(--text-primary) !important;
}

/* Chat Input styling */
.stChatInput {
    background: transparent !important;
    padding-bottom: 20px !important;
}

.stChatInput > div {
    background: rgba(25, 15, 45, 0.8) !important;
    border: 1px solid rgba(167, 139, 250, 0.25) !important;
    border-radius: 24px !important;
    box-shadow: 0 10px 30px rgba(124, 58, 237, 0.15) !important;
    backdrop-filter: blur(12px) !important;
    padding: 0.25rem 1rem !important;
    transition: all 0.3s ease !important;
}

.stChatInput > div:focus-within {
    border-color: var(--accent-primary) !important;
    box-shadow: 0 10px 30px rgba(124, 58, 237, 0.3) !important;
}

.stChatInput textarea {
    color: var(--text-primary) !important;
    font-size: 0.95rem !important;
}

/* Chat Message Bubbles */
.stChatMessage {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-color) !important;
    border-radius: 16px !important;
    backdrop-filter: blur(10px) !important;
    padding: 1.25rem !important;
    margin-bottom: 0.85rem !important;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1) !important;
    animation: fadeInUp 0.4s ease-out;
}

/* Headings typography */
h1, h2, h3, h4 {
    font-family: 'Outfit', sans-serif !important;
    color: var(--text-primary) !important;
}

/* Badge Mode */
.mode-badge {
    display: inline-block;
    background: linear-gradient(135deg, var(--accent-secondary), var(--accent-primary));
    color: white;
    padding: 4px 14px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
    margin-bottom: 0.75rem;
    box-shadow: 0 2px 10px var(--accent-glow);
}

/* Keyframe animations */
@keyframes pulse {
    0% { opacity: 0.6; }
    50% { opacity: 1; }
    100% { opacity: 0.6; }
}

@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(8px); }
    to { opacity: 1; transform: translateY(0); }
}

.status-dot {
    animation: pulse 2s infinite ease-in-out;
}

/* Custom file upload styling */
.stFileUploader > div {
    background: rgba(30, 20, 60, 0.2) !important;
    border: 1px dashed var(--border-color) !important;
    border-radius: 8px !important;
}

/* Scrollbar styling */
::-webkit-scrollbar {
    width: 6px;
    height: 6px;
}
::-webkit-scrollbar-track {
    background: var(--bg-primary);
}
::-webkit-scrollbar-thumb {
    background: var(--accent-secondary);
    border-radius: 4px;
}
</style>
"""
st.markdown(PREMIUM_CSS, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Imports from project modules
# ---------------------------------------------------------------------------
from chatbot import send_message_stream, GeminiQuotaError, get_api_key
from logger import (
    app_logger,
    auth_logger,
    chat_logger,
    knowledge_logger,
    medical_logger,
    research_logger,
    images_logger,
    perf_logger,
    api_logger,
    log_err
)
from knowledge_manager import (
    load_metadata,
    add_document,
    delete_document,
    get_watch_folders,
    rebuild_knowledge_base,
    set_watch_folders,
    sync_and_refresh_knowledge_base,
    get_documents_save_dir,
)
from rag_engine import query_relevant_chunks, format_rag_context, build_system_prompt_with_context
from chat_manager import (
    create_session,
    delete_session as delete_chat_session,
    export_chat_pdf,
    export_chat_txt,
    list_sessions,
    load_session,
    rename_session,
    update_session,
)
from web_search import (
    extract_weather_location,
    fallback_answer as fallback_web_answer,
    format_results_for_prompt,
    get_weather,
    is_realtime_query,
    search_web,
)
from auth.service import (
    authenticate_user,
    create_user as create_auth_user,
    get_user_profile,
    guest_profile,
    update_user_profile,
)
from database.storage import initialize_database
from multilingual.service import (
    SUPPORTED_LANGUAGES,
    VOICE_READY_CONFIG,
    build_language_instruction,
    build_model_user_message,
    prepare_language_context,
)
from multimodal.image_service import list_image_events, save_uploaded_image_event
from research.service import (
    format_papers_for_prompt,
    record_research_query,
    related_papers,
    search_papers,
    summarize_papers,
    timeline_rows,
)
from sentiment.service import (
    analyze_sentiment,
    build_sentiment_instruction,
    list_sentiment_events,
    record_sentiment,
    sentiment_badge_html,
    sentiment_summary,
)

# ---------------------------------------------------------------------------
# Constants & Local Fallback Data
# ---------------------------------------------------------------------------
LOCAL_GREETINGS = {
    "hi": "Hello! I'm your local fallback assistant. The remote AI service is currently unavailable, but I'm here to help you locally.",
    "hello": "Hello! I'm your local fallback assistant. The remote AI service is currently unavailable, but I'm here to help you locally.",
    "hey": "Hi there! I'm your local fallback assistant. The remote AI service is currently unavailable, but I can still help you.",
    "how are you": "I'm doing well, thank you! As a local fallback assistant, I'm running completely on your system.",
    "greetings": "Greetings! I'm your local fallback assistant. The remote AI is currently offline. How can I assist you?",
}

LOCAL_KNOWLEDGE_BASE = {
    "python": (
        "Python is a high-level, interpreted programming language known for its readability, simplicity, and versatility. "
        "It is widely used in web development, data science, artificial intelligence, machine learning, automation, and software prototyping."
    ),
    "machine learning": (
        "Machine Learning (ML) is a subset of artificial intelligence that enables computers to learn from data and improve their performance "
        "over time without being explicitly programmed."
    ),
    "artificial intelligence": (
        "Artificial Intelligence (AI) is the simulation of human intelligence processes by computer systems. "
        "These processes include learning, reasoning, and self-correction."
    ),
    "internet": (
        "The internet is a global system of interconnected computer networks that uses the Internet Protocol suite (TCP/IP) "
        "to link devices worldwide."
    ),
    "asthma": (
        "Asthma is a chronic respiratory condition characterized by inflammation and narrowing of the airways, "
        "which causes difficulty breathing, wheezing, shortness of breath, and coughing."
    ),
}

# System prompts for each mode
GENERAL_SYSTEM_PROMPT = (
    "You are 'OmniChat General Assistant', a friendly, knowledgeable, and professional AI assistant. "
    "Answer questions clearly and helpfully. You can discuss any topic."
)

KB_SYSTEM_PROMPT_TEMPLATE = (
    "You are 'OmniChat Knowledge Base Assistant', a helpful AI assistant that answers questions "
    "strictly using the provided document context.\n\n"
    "1. Answer the question using ONLY the facts and details provided in the UPLOADED DOCUMENTS CONTEXT below.\n"
    "2. If the answer cannot be found in the context, say 'Information not found in uploaded documents.' "
    "and then provide your best general knowledge answer clearly labeled as such.\n"
    "3. Cite the document source when referencing facts.\n"
)

IMAGE_ANALYSIS_SYSTEM_PROMPT = (
    "You are 'OmniChat Image Analyst', an expert AI that analyzes images. "
    "Describe what you see in detail, identify objects, text, patterns, and provide insights."
)

RESEARCH_SYSTEM_PROMPT = (
    "You are 'OmniChat Research Expert', a rigorous computer-science research assistant. "
    "Use the provided paper records first, cite paper titles and URLs, explain concepts clearly, "
    "suggest follow-up questions, and distinguish evidence from inference."
)

LIVE_SEARCH_SYSTEM_PROMPT = (
    "You are OmniChat AI with live web-search context. Answer using the live results below. "
    "Cite sources with markdown links. If the results are insufficient or contradictory, say so clearly."
)

ASSISTANT_MODES = {
    "General Assistant",
    "Knowledge Base Assistant",
    "Medical Assistant",
    "Research Assistant",
    "Image Analysis",
}

PAGE_MODES = {
    "Dashboard",
    "Knowledge Management",
    "Sentiment Analytics",
    "Settings",
}

MODE_OPTIONS = [
    "Dashboard",
    "General Assistant",
    "Knowledge Base Assistant",
    "Knowledge Management",
    "Medical Assistant",
    "Research Assistant",
    "Image Analysis",
    "Sentiment Analytics",
    "Settings",
]

# ---------------------------------------------------------------------------
# Session State Initialization
# ---------------------------------------------------------------------------
def init_session_state():
    """Initialize all session state variables."""
    defaults = {
        "messages": [],
        "gemini_history": [],
        "chat_mode": "General Assistant",
        "previous_mode": "General Assistant",
        "temp_images": [],
        "custom_api_key": "",
        "active_model_used": "",
        "fallback_language": "en",
        "image_gen_enabled": False,
        "auto_refresh_kb": True,
        "active_session_id": "",
        "authenticated_user": None,
        "user_profile": guest_profile(),
        "language_selector": "auto",
        "theme_mode": "Dark",
        "latest_sentiment": None,
        "last_language_context": None,
        "image_records": [],
        "image_upload_signature": [],
        "research_live_arxiv": True,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

initialize_database()
init_session_state()

if not st.session_state.active_session_id:
    session = create_session(mode=st.session_state.chat_mode)
    st.session_state.active_session_id = session["id"]


def get_active_user_id() -> str:
    """Return the current profile id, falling back to a guest profile."""
    profile = st.session_state.get("user_profile") or guest_profile()
    return str(profile.get("id", "guest"))


def apply_theme_overrides() -> None:
    """Apply light/dark CSS variable overrides without replacing the base UI."""
    if st.session_state.get("theme_mode", "Dark") != "Light":
        return
    st.markdown(
        """
        <style>
        :root {
            --bg-primary: #f8fafc;
            --bg-secondary: #eef2ff;
            --bg-card: rgba(255, 255, 255, 0.78);
            --accent-primary: #2563eb;
            --accent-secondary: #0891b2;
            --accent-glow: rgba(37, 99, 235, 0.18);
            --text-primary: #0f172a;
            --text-secondary: #475569;
            --text-muted: #64748b;
            --border-color: rgba(15, 23, 42, 0.12);
        }
        .stApp {
            background: linear-gradient(135deg, #f8fafc 0%, #eef2ff 55%, #ecfeff 100%) !important;
        }
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #ffffff 0%, #eef2ff 100%) !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


apply_theme_overrides()

# ---------------------------------------------------------------------------
# Mode Switch Handler — clears mode-specific state
# ---------------------------------------------------------------------------
def handle_mode_switch():
    """Clear mode-specific state when switching modes."""
    if st.session_state.chat_mode != st.session_state.previous_mode:
        st.session_state.messages = []
        st.session_state.gemini_history = []
        st.session_state.temp_images = []
        st.session_state.previous_mode = st.session_state.chat_mode

# ---------------------------------------------------------------------------
# Helper: Date/Time detection
# ---------------------------------------------------------------------------
def is_datetime_query(text: str) -> bool:
    """Check if the user is asking about date or time."""
    patterns = [
        r"\b(what|whats|what's)\s+(is\s+)?(the\s+)?(current\s+)?(date|time|day|month|year)\b",
        r"\b(today'?s?\s+date|current\s+time|current\s+date)\b",
        r"\b(what\s+day\s+is\s+it|what\s+time\s+is\s+it)\b",
        r"\b(tell\s+me\s+the\s+(date|time))\b",
    ]
    text_lower = text.lower().strip()
    return any(re.search(p, text_lower) for p in patterns)


def get_datetime_response() -> str:
    """Return a formatted date/time response."""
    now = datetime.datetime.now()
    return (
        f"📅 **Current Date:** {now.strftime('%A, %B %d, %Y')}\n\n"
        f"🕐 **Current Time:** {now.strftime('%I:%M:%S %p')}\n\n"
        f"📆 **Day of the Week:** {now.strftime('%A')}\n\n"
        f"🗓️ **Month:** {now.strftime('%B')} | **Year:** {now.year}"
    )

# ---------------------------------------------------------------------------
# Helper: Greeting detection
# ---------------------------------------------------------------------------
def is_general_conversation(text: str) -> bool:
    """Check if the input is a greeting or basic conversational prompt."""
    cleaned = text.strip().lower().rstrip("?.!")
    greetings = {
        "hi", "hello", "hey", "good morning", "good evening", "good afternoon",
        "greetings", "howdy", "sup", "yo", "namaste", "hola",
        "who are you", "what are you", "what can you do",
        "talk in hindi", "speak hindi", "speak in english",
    }
    return cleaned in greetings

# ---------------------------------------------------------------------------
# Helper: Image generation query detection
# ---------------------------------------------------------------------------
def is_image_gen_query(text: str) -> bool:
    """Check if the user wants to generate/draw/create an image."""
    patterns = [
        r"\b(draw|generate|create|make|design|sketch|paint|render)\b.*\b(image|picture|photo|art|illustration|icon|logo|poster)\b",
        r"\b(image|picture|photo)\b.*\b(of|for|about|showing)\b",
    ]
    text_lower = text.lower().strip()
    return any(re.search(p, text_lower) for p in patterns)


def save_current_chat_session():
    """Persist the active chat session."""
    try:
        update_session(
            st.session_state.active_session_id,
            mode=st.session_state.chat_mode,
            messages=st.session_state.messages,
            gemini_history=st.session_state.gemini_history,
        )
    except Exception as exc:
        print(f"[Chat Session Save Error] {exc}", file=sys.stderr)


def render_streamed_response(stream) -> str:
    """Render streamed Gemini output in the current assistant chat bubble."""
    if stream is None:
        return ""

    full_text = ""
    placeholder = st.empty()
    try:
        for chunk in stream:
            if chunk is None:
                continue
            full_text += str(chunk)
            placeholder.markdown(full_text)
    except Exception as exc:
        print(f"[Stream Render Error] {exc}", file=sys.stderr)
        placeholder.markdown(
            full_text + "\n\n⚠️ Stream interrupted: " + str(exc)
        )
    return full_text


def answer_live_query(user_message: str) -> tuple[any, str | None]:
    """Answer a real-time query with weather/search data and Gemini synthesis."""
    weather_location = extract_weather_location(user_message)
    if weather_location:
        weather = get_weather(weather_location)
        answer = f"Live weather result: **{weather}**"
        return None, answer

    query = user_message
    if "ipl" in user_message.lower() and "yesterday" in user_message.lower():
        query = f"{user_message} latest IPL result {datetime.datetime.now().date()}"
    results = search_web(query, max_results=5)
    context = format_results_for_prompt(query, results)
    try:
        stream = send_message_stream(
            history=st.session_state.gemini_history[:-1],
            user_message=user_message,
            system_instruction=f"{LIVE_SEARCH_SYSTEM_PROMPT}\n\n{context}",
            max_output_tokens=2048,
        )
        # Pull first chunk to initialize stream
        iterator = iter(stream)
        first_chunk = next(iterator, None)
        def stream_iterator():
            if first_chunk is not None:
                yield first_chunk
            for chunk in iterator:
                yield chunk
        return stream_iterator(), None
    except Exception as exc:
        print(f"[Live Search Gemini Error] {exc}", file=sys.stderr)
        answer = fallback_web_answer(user_message, results)
        return None, answer

# ---------------------------------------------------------------------------
# Helper: Local fallback
# ---------------------------------------------------------------------------
def handle_local_fallback(user_message: str) -> str:
    """Generate a response using local data when Gemini is unavailable."""
    cleaned = user_message.strip().lower().rstrip("?.!")

    # Check greetings
    for key, response in LOCAL_GREETINGS.items():
        if cleaned == key or cleaned.startswith(key):
            return response

    # Check date/time
    if is_datetime_query(user_message):
        return get_datetime_response()

    # Check knowledge base
    for topic, answer in LOCAL_KNOWLEDGE_BASE.items():
        if topic in cleaned:
            prefixes = [
                "Based on my offline knowledge base, here's what I know:",
                "Here is some information from my local database:",
                "From my built-in knowledge:",
            ]
            return f"{random.choice(prefixes)}\n\n{answer}"

    # Generic fallback
    return (
        "⚠️ **Gemini API is currently unavailable.** I'm running in local fallback mode.\n\n"
        "I can help with:\n"
        "1. Basic greetings and conversation\n"
        "2. Date and time queries\n"
        "3. Some general knowledge topics (Python, ML, AI, etc.)\n\n"
        "Please check your API key in Settings or try again later."
    )


def build_enterprise_system_prompt(
    base_prompt: str,
    sentiment: dict | None = None,
    language_context: dict | None = None,
) -> str:
    """Append customer sentiment and multilingual policy to a task prompt."""
    sections = [base_prompt]
    if sentiment:
        sections.append(build_sentiment_instruction(sentiment))
    if language_context:
        sections.append(build_language_instruction(language_context))
    return "\n\n".join(sections)


def render_auth_panel() -> None:
    """Render sidebar account controls."""
    profile = st.session_state.get("user_profile") or guest_profile()
    with st.expander("👤 Account Profile", expanded=False):
        st.caption(f"Active profile: {profile.get('display_name', 'Guest')}")
        if st.session_state.get("authenticated_user"):
            if st.button("Sign out", key="btn_sign_out", use_container_width=True):
                st.session_state.authenticated_user = None
                st.session_state.user_profile = guest_profile()
                st.rerun()
            return

        sign_in_tab, create_tab = st.tabs(["Sign in", "Create"])
        with sign_in_tab:
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            if st.button("Sign in", key="btn_login", use_container_width=True):
                user = authenticate_user(username, password)
                if user:
                    st.session_state.authenticated_user = user
                    st.session_state.user_profile = user
                    st.session_state.language_selector = user.get("preferred_language", "en")
                    st.session_state.theme_mode = user.get("theme", "Dark")
                    st.success("Signed in.")
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
        with create_tab:
            new_username = st.text_input("New username", key="create_username")
            new_name = st.text_input("Display name", key="create_display_name")
            new_password = st.text_input("New password", type="password", key="create_password")
            ok, message = True, ""
            if st.button("Create account", key="btn_create_account", use_container_width=True):
                ok, message = create_auth_user(new_username, new_password, new_name)
                if ok:
                    st.success(message)
                else:
                    st.error(message)


def render_dashboard_page() -> None:
    """Render high-level product and operational metrics."""
    metadata = load_metadata()
    sentiment_stats = sentiment_summary()
    image_rows = list_image_events(limit=5)
    sessions = list_sessions()
    generated_count = len(list(Path("generated_images").glob("*.png"))) if Path("generated_images").exists() else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Chat sessions", len(sessions))
    col2.metric("KB documents", len(metadata.get("files", {})))
    col3.metric("KB chunks", metadata.get("total_chunks", 0))
    col4.metric("Generated images", generated_count)

    col5, col6, col7 = st.columns(3)
    counts = sentiment_stats["counts"]
    col5.metric("Positive", counts.get("Positive", 0))
    col6.metric("Negative", counts.get("Negative", 0))
    col7.metric("Neutral", counts.get("Neutral", 0))

    st.subheader("Service status")
    status_cols = st.columns(3)
    status_cols[0].success("Gemini client configured" if os.environ.get("GEMINI_API_KEY") or st.session_state.get("custom_api_key") else "Gemini key needed")
    status_cols[1].info(f"Vector index chunks: {metadata.get('total_chunks', 0)}")
    try:
        from medical_vector_store import is_medical_db_ready

        status_cols[2].success("Medical DB ready" if is_medical_db_ready() else "Medical DB not built")
    except Exception as exc:
        status_cols[2].warning(f"Medical status unavailable: {exc}")

    st.subheader("Sentiment mix")
    if sentiment_stats["total"]:
        try:
            import plotly.express as px

            rows = [{"label": key, "count": value} for key, value in counts.items()]
            fig = px.pie(rows, names="label", values="count", hole=0.55)
            fig.update_layout(height=320, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)
        except Exception:
            st.dataframe(counts, use_container_width=True)
    else:
        st.info("Sentiment analytics will appear after customer messages are sent.")

    st.subheader("Recent image history")
    if image_rows:
        st.dataframe(
            [
                {
                    "filename": row["filename"],
                    "size": f"{row.get('width')}x{row.get('height')}",
                    "ocr_preview": (row.get("ocr_text") or "")[:90],
                    "created_at": row["created_at"],
                }
                for row in image_rows
            ],
            use_container_width=True,
        )
    else:
        st.caption("No images uploaded yet.")


def render_knowledge_management_page() -> None:
    """Render a full knowledge-base operations page."""
    st.subheader("Knowledge base operations")
    uploaded_files = st.file_uploader(
        "Upload PDF, DOCX, TXT, CSV, or image files",
        type=["pdf", "docx", "txt", "csv", "png", "jpg", "jpeg", "webp", "gif"],
        accept_multiple_files=True,
        key="kb_page_uploader",
    )
    if uploaded_files and st.button("Index selected files", key="btn_page_index", use_container_width=True):
        progress = st.progress(0)
        successes = 0
        for idx, file in enumerate(uploaded_files, 1):
            with st.spinner(f"Indexing {file.name}..."):
                success, msg = add_document(file.name, file.getvalue())
                if success:
                    successes += 1
                    st.success(f"✅ '{file.name}': {msg}")
                else:
                    st.error(f"❌ Failed to index '{file.name}': {msg}")
            progress.progress(idx / len(uploaded_files))
        st.success(f"Indexed {successes} of {len(uploaded_files)} file(s).")

    metadata = load_metadata()
    files = metadata.get("files", {})
    col1, col2, col3 = st.columns(3)
    col1.metric("Documents", len(files))
    col2.metric("Chunks", metadata.get("total_chunks", 0))
    col3.metric("Embeddings", metadata.get("total_embeddings", 0))

    if st.button("Refresh vector database", key="btn_page_refresh", use_container_width=True):
        with st.spinner("Refreshing knowledge base..."):
            changed = sync_and_refresh_knowledge_base()
        st.success("Knowledge base updated." if changed else "Knowledge base already in sync.")

    if st.button("Rebuild vector database", key="btn_page_rebuild", use_container_width=True):
        with st.spinner("Rebuilding FAISS index..."):
            rebuild_knowledge_base()
        st.success("Vector database rebuilt.")

    st.subheader("Indexed documents")
    if files:
        for filename, info in files.items():
            col_name, col_chunks, col_refresh, col_delete = st.columns([4, 2, 1, 1])
            col_name.markdown(f"**{filename}**")
            col_chunks.caption(f"{info.get('chunks_count', 0)} chunks")
            
            if col_refresh.button("Refresh", key=f"page_ref_{filename}"):
                with st.spinner(f"Refreshing {filename}..."):
                    save_dir = get_documents_save_dir()
                    file_path = os.path.join(save_dir, filename)
                    if os.path.exists(file_path):
                        with open(file_path, "rb") as f:
                            file_bytes = f.read()
                        delete_document(filename)
                        success, msg = add_document(filename, file_bytes)
                        if success:
                            st.success(f"Refreshed {filename}")
                        else:
                            st.error(f"Failed to refresh: {msg}")
                        st.rerun()
                    else:
                        st.error("Source file not found on disk.")
                        
            if col_delete.button("Delete", key=f"page_del_{filename}"):
                delete_document(filename)
                st.rerun()
    else:
        st.info("No documents are indexed yet.")

    st.subheader("Automatic indexing")
    folders_text = st.text_area(
        "Watched folders, one per line",
        value="\n".join(get_watch_folders()),
        key="page_watch_folders",
    )
    save_col, sync_col = st.columns(2)
    if save_col.button("Save watched folders", key="btn_page_save_watch", use_container_width=True):
        set_watch_folders(folders_text.splitlines())
        st.success("Watched folders saved.")
    if sync_col.button("Sync watched folders", key="btn_page_sync_watch", use_container_width=True):
        changed = sync_and_refresh_knowledge_base()
        st.success("Knowledge base updated." if changed else "Already up to date.")


def render_research_discovery_panel() -> None:
    """Render research search controls above the research chat."""
    with st.expander("Research dashboard", expanded=True):
        query = st.text_input("Search arXiv Computer Science papers", key="research_query")
        col_a, col_b = st.columns([1, 1])
        st.session_state.research_live_arxiv = col_a.checkbox(
            "Use live arXiv when available",
            value=st.session_state.get("research_live_arxiv", True),
            key="research_live_toggle",
        )
        max_results = col_b.slider("Results", 3, 12, 6, key="research_result_count")
        if st.button("Search papers", key="btn_research_search", use_container_width=True) and query:
            papers = search_papers(
                query,
                max_results=max_results,
                include_live_arxiv=st.session_state.research_live_arxiv,
            )
            st.session_state["research_last_results"] = papers
            record_research_query(get_active_user_id(), query, len(papers))

        papers = st.session_state.get("research_last_results", [])
        if papers:
            st.markdown(summarize_papers(papers), unsafe_allow_html=True)
            try:
                import pandas as pd
                import plotly.express as px

                rows = timeline_rows(papers)
                df = pd.DataFrame(rows)
                fig = px.scatter(
                    df,
                    x="date",
                    y="category",
                    size="relevance",
                    hover_name="title",
                    title="Paper timeline",
                )
                fig.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=20))
                st.plotly_chart(fig, use_container_width=True)
            except Exception:
                st.caption("Timeline visualization requires pandas and plotly.")


def render_sentiment_analytics_page() -> None:
    """Render sentiment history and charts."""
    stats = sentiment_summary()
    counts = stats["counts"]
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Messages", stats["total"])
    col2.metric("Positive Sentiment", counts.get("Positive", 0))
    col3.metric("Negative Sentiment", counts.get("Negative", 0))
    col4.metric("Neutral Sentiment", counts.get("Neutral", 0))

    events = list_sentiment_events(limit=250)
    if not events:
        st.info("No sentiment records yet. Send a few customer messages first.")
        return

    try:
        import pandas as pd
        import plotly.express as px

        df = pd.DataFrame(events)
        
        # Ensure emotion column exists
        if "emotion" not in df.columns:
            df["emotion"] = "Neutral"

        chart_col1, chart_col2 = st.columns(2)
        with chart_col1:
            fig_sent = px.histogram(df, x="label", color="label", title="Sentiment Distribution",
                                    color_discrete_map={"Positive": "#34d399", "Negative": "#f87171", "Neutral": "#9ca3af"})
            fig_sent.update_layout(height=320, margin=dict(l=20, r=20, t=50, b=20))
            st.plotly_chart(fig_sent, use_container_width=True)
            
        with chart_col2:
            emo_counts = df["emotion"].value_counts().reset_index()
            emo_counts.columns = ["emotion", "count"]
            fig_emo = px.pie(emo_counts, names="emotion", values="count", title="Customer Emotions Mix", hole=0.4)
            fig_emo.update_layout(height=320, margin=dict(l=20, r=20, t=50, b=20))
            st.plotly_chart(fig_emo, use_container_width=True)

        st.subheader("Historical Analytics")
        display_df = df.copy()
        display_df["confidence"] = display_df["confidence"].apply(lambda x: f"{x:.1%}")
        st.dataframe(
            display_df[["created_at", "label", "emotion", "confidence", "message"]].head(100),
            use_container_width=True,
        )
    except Exception as exc:
        st.error(f"Error rendering charts: {exc}")
        st.dataframe(events, use_container_width=True)


def render_settings_page() -> None:
    """Render application and profile settings."""
    profile = st.session_state.get("user_profile") or guest_profile()
    
    # Custom CSS style for settings cards, badges, and toggle
    st.markdown("""
    <style>
    .settings-card {
        background: rgba(30, 20, 60, 0.4);
        border: 1px solid rgba(167, 139, 250, 0.15);
        border-radius: 12px;
        padding: 1.5rem;
        margin-bottom: 1.5rem;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
        backdrop-filter: blur(8px);
    }
    .provider-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
    }
    .provider-title {
        font-family: 'Outfit', sans-serif;
        font-size: 1.25rem;
        font-weight: 700;
        color: var(--text-primary);
    }
    .model-badge {
        display: inline-block;
        background: linear-gradient(135deg, var(--accent-secondary), var(--accent-primary));
        color: white !important;
        padding: 3px 12px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        border: 1px solid rgba(255, 255, 255, 0.15);
    }
    .status-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.4rem;
        font-size: 0.85rem;
        font-weight: 600;
    }
    .status-badge.connected {
        color: var(--success);
    }
    .status-badge.disconnected {
        color: var(--danger);
    }
    .latency-val {
        font-size: 0.85rem;
        color: var(--text-secondary);
        font-weight: 500;
    }
    .last-checked {
        font-size: 0.75rem;
        color: var(--text-muted);
    }
    </style>
    """, unsafe_allow_html=True)
    
    # 1. AI Provider Card
    st.markdown('<div class="settings-card">', unsafe_allow_html=True)
    st.markdown('<div class="provider-header"><span class="provider-title">☁️ AI Provider</span></div>', unsafe_allow_html=True)
    
    # Determine model and connection info
    model_name = "Gemini 2.5 Flash Lite"
    status_label = st.session_state.get("settings_conn_status", "Disconnected")
    status_class = "connected" if status_label == "Connected" else "disconnected"
    latency_label = st.session_state.get("settings_conn_latency", "N/A")
    checked_label = st.session_state.get("settings_conn_checked", "Never")
    
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        st.markdown("**Provider:** Google AI Studio")
        st.markdown(f"**Current Model:** <span class=\"model-badge\">{model_name}</span>", unsafe_allow_html=True)
    with col_p2:
        status_dot_color = "var(--success)" if status_label == "Connected" else "var(--danger)"
        st.markdown(
            f"**Status:** <span class=\"status-badge {status_class}\"><span class=\"status-dot\" style=\"background-color:{status_dot_color}; box-shadow: 0 0 8px {status_dot_color};\"></span>{status_label}</span>",
            unsafe_allow_html=True
        )
        st.markdown(f"**Latency:** <span class=\"latency-val\">{latency_label}</span>", unsafe_allow_html=True)
        st.markdown(f"<span class=\"last-checked\">Last Checked: {checked_label}</span>", unsafe_allow_html=True)
        
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 2. Connection Actions
    col_t1, col_t2 = st.columns([1, 2])
    with col_t1:
        if st.button("🔌 Test Connection", key="btn_test_conn", use_container_width=True):
            with st.spinner("Testing..."):
                t_start = time.perf_counter()
                from chatbot import test_api_connectivity
                gemini_key = st.session_state.get("custom_api_key") or os.environ.get("GEMINI_API_KEY")
                diag = test_api_connectivity(gemini_key if gemini_key else None)
                t_end = time.perf_counter()
                latency_ms = (t_end - t_start) * 1000
                
                if diag["status"] == "Online":
                    st.session_state.settings_conn_status = "Connected"
                    st.session_state.settings_conn_latency = f"{latency_ms:.0f} ms"
                else:
                    st.session_state.settings_conn_status = "Disconnected"
                    st.session_state.settings_conn_latency = "Timeout"
                st.session_state.settings_conn_checked = datetime.datetime.now().strftime("%I:%M:%S %p")
                st.rerun()
                
    st.markdown("---")
    
    # 3. Profile Card
    st.markdown('<div class="settings-card">', unsafe_allow_html=True)
    st.markdown('<div class="provider-header"><span class="provider-title">👤 User Profile Settings</span></div>', unsafe_allow_html=True)
    display_name = st.text_input("Display name", value=profile.get("display_name", "Guest"))
    role = st.text_input("Role", value=profile.get("role", "Customer Support Agent"))
    selected_language = st.selectbox(
        "Preferred response language",
        list(SUPPORTED_LANGUAGES.keys()),
        index=list(SUPPORTED_LANGUAGES.keys()).index(st.session_state.get("language_selector", "auto")),
        format_func=lambda key: SUPPORTED_LANGUAGES[key],
        key="settings_language_selector",
    )
    
    # Theme segmented toggle: 🌙 Dark | ☀ Light | 💻 System
    theme_options_map = {
        "🌙 Dark": "Dark",
        "☀ Light": "Light",
        "💻 System": "Dark" # System default fallback mapped safely to Dark
    }
    
    current_theme = st.session_state.get("theme_mode", "Dark")
    default_idx = 0
    if current_theme == "Light":
        default_idx = 1
        
    selected_theme_label = st.radio(
        "Theme Mode Selection",
        ["🌙 Dark", "☀ Light", "💻 System"],
        index=default_idx,
        horizontal=True,
        key="settings_theme_mode_selector"
    )
    selected_theme = theme_options_map[selected_theme_label]
    
    if st.button("Save Profile Settings", key="btn_save_settings", use_container_width=True):
        st.session_state.language_selector = selected_language
        st.session_state.theme_mode = selected_theme
        if profile.get("id") != "guest":
            update_user_profile(
                profile["id"],
                display_name=display_name,
                role=role,
                preferred_language=selected_language,
                theme=selected_theme,
            )
            st.session_state.user_profile = get_user_profile(profile["id"]) or profile
        else:
            profile.update(
                {
                    "display_name": display_name,
                    "role": role,
                    "preferred_language": selected_language,
                    "theme": selected_theme,
                }
            )
            st.session_state.user_profile = profile
        st.success("Profile saved successfully!")
    st.markdown('</div>', unsafe_allow_html=True)
    
    # 4. Advanced Settings (Collapsible - Gemini and OpenAI Keys)
    with st.expander("🛠️ Advanced Settings", expanded=False):
        st.caption("Advanced AI Provider Settings & Security Credentials")
        api_key_input = st.text_input(
            "🔑 Gemini API Key (Overrides system config)",
            value=st.session_state.get("custom_api_key", ""),
            type="password",
            key="api_key_field_main",
        )
        if api_key_input != st.session_state.get("custom_api_key", ""):
            st.session_state.custom_api_key = api_key_input
            
        openai_key_input = st.text_input(
            "OpenAI API Key (for DALL-E 3 image generation)",
            value=st.session_state.get("openai_api_key", ""),
            type="password",
            help="Provide your OpenAI API key to enable high-quality DALL-E 3 image generation.",
            key="openai_key_field_main"
        )
        if openai_key_input != st.session_state.get("openai_api_key", ""):
            st.session_state.openai_api_key = openai_key_input
            
    st.subheader("Voice-ready architecture")
    st.json(VOICE_READY_CONFIG)
    
    st.subheader("Runtime")
    st.caption("Secrets are read from environment variables or the password field in the sidebar.")

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------
import os
try:
    import psutil
    process = psutil.Process(os.getpid())
    mem_usage = f"{process.memory_info().rss / 1024 / 1024:.0f} MB"
except Exception:
    mem_usage = "N/A"

model_used = st.session_state.get("active_model_used") or "gemini-1.5-flash"
provider_used = "Google Gemini"

header_html = f"""
<div class="omnichat-header">
    <div class="header-left">
        <h1>🧠 OmniChat AI</h1>
        <p>Enterprise Customer Service Platform</p>
    </div>
    <div class="header-right">
        <div class="header-metric">
            <span class="metric-label">Model:</span>
            <span class="metric-value">{model_used}</span>
        </div>
        <div class="header-metric">
            <span class="metric-label">Provider:</span>
            <span class="metric-value">{provider_used}</span>
        </div>
        <div class="header-metric">
            <span class="metric-label">RAM:</span>
            <span class="metric-value">{mem_usage}</span>
        </div>
        <div class="header-status">
            <span class="status-dot"></span> Active
        </div>
        <div class="header-actions">
            <span class="header-btn" title="Dark Mode Active">🌙</span>
            <span class="header-btn" title="Notifications">🔔</span>
            <div class="header-avatar" title="User Profile">U</div>
        </div>
    </div>
</div>
"""
st.markdown(header_html, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown("## 🎛️ Control Panel")
    render_auth_panel()

    # Mode selector
    chat_mode = st.selectbox(
        "🔀 Select Mode",
        MODE_OPTIONS,
        key="chat_mode",
        on_change=handle_mode_switch,
    )

    # Show active mode badge
    mode_icons = {
        "Dashboard": "DB",
        "General Assistant": "💬",
        "Knowledge Base Assistant": "📚",
        "Knowledge Management": "KB",
        "Medical Assistant": "🏥",
        "Research Assistant": "RX",
        "Image Analysis": "🖼️",
        "Sentiment Analytics": "SA",
        "Settings": "SET",
    }
    st.markdown(
        f'<div class="mode-badge">{mode_icons.get(chat_mode, "🤖")} {chat_mode}</div>',
        unsafe_allow_html=True,
    )

    st.divider()

    with st.expander("Chat Sessions", expanded=False):
        sessions = list_sessions()
        session_labels = {
            f"{item['title']} ({item['mode']})": item["id"]
            for item in sessions
        }
        active_label = next(
            (label for label, sid in session_labels.items() if sid == st.session_state.active_session_id),
            None,
        )
        if session_labels:
            selected_label = st.selectbox(
                "Open previous chat",
                list(session_labels.keys()),
                index=list(session_labels.keys()).index(active_label) if active_label in session_labels else 0,
                key="session_picker",
            )
            selected_id = session_labels[selected_label]
            if selected_id != st.session_state.active_session_id and st.button("Open Chat", key="btn_open_session"):
                loaded = load_session(selected_id)
                if loaded:
                    st.session_state.active_session_id = loaded["id"]
                    st.session_state.messages = loaded.get("messages", [])
                    st.session_state.gemini_history = loaded.get("gemini_history", [])
                    st.session_state.previous_mode = st.session_state.chat_mode
                    st.rerun()

        new_title = st.text_input("Session title", value="New chat", key="new_session_title")
        col_new, col_save = st.columns(2)
        with col_new:
            if st.button("New Chat", key="btn_new_session", use_container_width=True):
                save_current_chat_session()
                session = create_session(mode=chat_mode, title=new_title or "New chat")
                st.session_state.active_session_id = session["id"]
                st.session_state.messages = []
                st.session_state.gemini_history = []
                st.session_state.temp_images = []
                st.rerun()
        with col_save:
            if st.button("Save Chat", key="btn_save_session", use_container_width=True):
                save_current_chat_session()
                st.success("Saved.")

        rename_title = st.text_input("Rename active chat", value="", key="rename_session_title")
        col_rename, col_delete = st.columns(2)
        with col_rename:
            if st.button("Rename", key="btn_rename_session", use_container_width=True):
                if rename_session(st.session_state.active_session_id, rename_title):
                    st.success("Renamed.")
                    st.rerun()
        with col_delete:
            if st.button("Delete", key="btn_delete_session", use_container_width=True):
                delete_chat_session(st.session_state.active_session_id)
                session = create_session(mode=chat_mode)
                st.session_state.active_session_id = session["id"]
                st.session_state.messages = []
                st.session_state.gemini_history = []
                st.rerun()

    # ---- MODE-SPECIFIC SIDEBAR WIDGETS ----

    # Knowledge Base: document management (ONLY in KB mode)
    if chat_mode == "Knowledge Base Assistant":
        with st.expander("📂 Document Management", expanded=True):
            uploaded_file = st.file_uploader(
                "Upload a document",
                type=["pdf", "docx", "txt", "csv", "png", "jpg", "jpeg", "webp", "gif"],
                key="kb_uploader",
                help="PDF, DOCX, TXT, CSV, or common images (processed via OCR)"
            )
            if uploaded_file is not None:
                if st.button("📥 Index Document", key="btn_index"):
                    with st.spinner("Processing and indexing..."):
                        success, msg = add_document(uploaded_file.name, uploaded_file.getvalue())
                        if success:
                            st.success(f"✅ '{uploaded_file.name}' indexed successfully!")
                        else:
                            st.error(f"❌ Failed to index document: {msg}")

            # Show indexed files
            metadata = load_metadata()
            files = metadata.get("files", {})
            if files:
                st.markdown(f"**📊 Indexed:** {len(files)} file(s), {metadata.get('total_chunks', 0)} chunks")
                for fname in list(files.keys()):
                    col1, col2, col3 = st.columns([4, 1, 1])
                    col1.markdown(f"📄 {fname}")
                    
                    if col2.button("🔄", key=f"ref_{fname}", help="Refresh"):
                        with st.spinner("Refreshing..."):
                            save_dir = get_documents_save_dir()
                            file_path = os.path.join(save_dir, fname)
                            if os.path.exists(file_path):
                                with open(file_path, "rb") as f:
                                    file_bytes = f.read()
                                delete_document(fname)
                                add_document(fname, file_bytes)
                                st.rerun()
                                
                    if col3.button("🗑️", key=f"del_{fname}", help="Delete"):
                        delete_document(fname)
                        st.rerun()
            else:
                st.info("No documents indexed yet. Upload a file above.")

            if st.button("🔄 Rebuild Index", key="btn_rebuild"):
                with st.spinner("Rebuilding..."):
                    rebuild_knowledge_base()
                st.success("Rebuilt index.")

            # Sidebar: Image Generation Settings (Step 11)
            if chat_mode in ["General Assistant", "Image Analysis"]:
                st.markdown("---")
                st.markdown("### 🎨 Image Generation Settings")
                
                from image_pipeline.optimizer import SUPPORTED_STYLES
                st.selectbox(
                    "Style override",
                    ["Auto"] + SUPPORTED_STYLES,
                    index=0,
                    key="img_style_override"
                )
                
                st.selectbox(
                    "Aspect Ratio",
                    ["Auto", "1:1", "16:9", "9:16", "3:4"],
                    index=0,
                    key="img_ar_override"
                )
                
                st.selectbox(
                    "Quality level",
                    ["Standard", "HD", "Ultra"],
                    index=0,
                    key="img_quality_override"
                )
                
                st.selectbox(
                    "Preferred model provider",
                    [
                        "Auto",
                        "Google Imagen 3",
                        "OpenAI DALL-E 3",
                        "Stability AI",
                        "Replicate",
                        "Fal.ai",
                        "HuggingFace (FLUX / SDXL)",
                        "Pollinations.ai (Flux Fallback)"
                    ],
                    index=0,
                    key="img_provider_override"
                )
                
                st.toggle(
                    "Show prompt preview before generation",
                    value=False,
                    key="img_preview_enabled"
                )

            # Sidebar: History of Generated Images
            st.markdown("---")
            st.markdown("### 🎨 Generated Images History")
            try:
                from database.storage import list_image_generation_history
                history_records = list_image_generation_history(limit=6)
                if history_records:
                    for s_idx, record in enumerate(history_records):
                        col_i_img, col_i_btn = st.columns([3, 1])
                        if os.path.exists(record["filepath"]):
                            col_i_img.image(record["filepath"], caption=record["style"], use_container_width=True)
                            try:
                                with open(record["filepath"], "rb") as f:
                                    file_data = f.read()
                                col_i_btn.download_button(
                                    "📥",
                                    data=file_data,
                                    file_name=os.path.basename(record["filepath"]),
                                    mime="image/png",
                                    key=f"side_dl_{s_idx}",
                                )
                            except Exception:
                                pass
                        else:
                            col_i_img.caption(f"Missing: {record['original_prompt'][:15]}")
                else:
                    st.caption("No images generated yet.")
            except Exception as e:
                st.caption(f"Error loading image history: {e}")

        with st.expander("Watched Folders", expanded=False):
            current_folders = "\n".join(get_watch_folders())
            folders_text = st.text_area(
                "One local folder per line",
                value=current_folders,
                key="watch_folders_text",
                help="Supported files in these folders are copied into the KB and incrementally indexed.",
            )
            col_watch_save, col_watch_sync = st.columns(2)
            with col_watch_save:
                if st.button("Save Folders", key="btn_save_watch", use_container_width=True):
                    set_watch_folders(folders_text.splitlines())
                    st.success("Watch folders saved.")
            with col_watch_sync:
                if st.button("Sync Now", key="btn_sync_watch", use_container_width=True):
                    with st.spinner("Syncing watched folders..."):
                        changed = sync_and_refresh_knowledge_base()
                        st.success("Knowledge base updated." if changed else "Already up to date.")

        # Auto-refresh check
        if st.session_state.get("auto_refresh_kb", False):
            try:
                sync_and_refresh_knowledge_base()
            except Exception:
                pass

    # Medical Assistant: status (ONLY in Medical mode)
    if chat_mode == "Medical Assistant":
        with st.expander("🏥 Medical Database", expanded=False):
            try:
                from medical_vector_store import is_medical_db_ready, build_medical_vector_store
                if is_medical_db_ready():
                    st.success("✅ Medical Database Ready")
                else:
                    st.warning("⚠️ Medical Database not built yet.")
                    if st.button("🔨 Build Medical DB", key="btn_build_med"):
                        with st.spinner("Building MedQuAD index (this may take a few minutes)..."):
                            build_medical_vector_store()
                            st.success("Medical database built!")
                            st.rerun()
            except Exception as e:
                st.error(f"Medical DB error: {e}")

    # Image Analysis: info (ONLY in Image mode)
    if chat_mode == "Image Analysis":
        st.info("📸 Upload an image below the chat and ask questions about it.")

    st.divider()

    # ---- SETTINGS (shared) ----
    with st.expander("⚙️ Settings", expanded=False):
        # API Key
        api_key_input = st.text_input(
            "🔑 Gemini API Key",
            value=st.session_state.get("custom_api_key", ""),
            type="password",
            key="api_key_field",
        )
        if api_key_input != st.session_state.get("custom_api_key", ""):
            st.session_state.custom_api_key = api_key_input

        selected_sidebar_language = st.selectbox(
            "Response language",
            list(SUPPORTED_LANGUAGES.keys()),
            index=list(SUPPORTED_LANGUAGES.keys()).index(st.session_state.get("language_selector", "auto")),
            format_func=lambda key: SUPPORTED_LANGUAGES[key],
            key="sidebar_language_selector",
        )
        st.session_state.language_selector = selected_sidebar_language

        selected_sidebar_theme = st.radio(
            "Theme",
            ["Dark", "Light"],
            index=0 if st.session_state.get("theme_mode", "Dark") == "Dark" else 1,
            horizontal=True,
            key="sidebar_theme_mode",
        )
        st.session_state.theme_mode = selected_sidebar_theme

        if st.button("🔍 Test API Key", key="btn_test_api"):
            with st.spinner("Testing..."):
                from chatbot import test_api_connectivity
                diag = test_api_connectivity(api_key_input if api_key_input else None)
                if diag["status"] == "Online":
                    st.success(f"✅ API Online (Key: {diag['key_masked']})")
                else:
                    st.error(f"❌ {diag['status']}: {diag.get('error_message', 'Unknown error')[:200]}")

        # Model info
        if st.session_state.get("active_model_used"):
            st.markdown(f"🤖 **Active Model:** `{st.session_state.active_model_used}`")

    # ---- ACTIONS (shared) ----
    st.divider()
    with st.expander("🛠️ Quick Actions", expanded=False):
        if st.button("🗑️ Clear Chat", use_container_width=True, key="btn_clear"):
            st.session_state.messages = []
            st.session_state.gemini_history = []
            st.session_state.temp_images = []
            st.rerun()
        
        st.markdown('<div style="text-align:center; margin:10px 0; color:var(--text-secondary); font-size:0.85rem; border-top:1px solid var(--border-color); padding-top:10px;">Export Conversation</div>', unsafe_allow_html=True)
        if st.session_state.messages:
            export_text = export_chat_txt(st.session_state.messages)
            export_pdf = export_chat_pdf(st.session_state.messages)
            
            # Inline helpers for Markdown and HTML exports
            md_content = "\n".join(f"### {m['role'].upper()}\n\n{m['content']}\n" for m in st.session_state.messages)
            
            body_html = "".join(
                f"<div class='msg {m['role']}' style='margin-bottom:15px; padding:12px; border-radius:8px; border:1px solid rgba(167,139,250,0.15); background:rgba(30,20,60,0.7);'>"
                f"<strong>{m['role'].upper()}:</strong><p>{m['content']}</p></div>"
                for m in st.session_state.messages
            )
            html_content = f"<html><head><title>OmniChat Export</title><style>body {{ font-family:sans-serif; background:#0f0a1a; color:#e2e8f0; padding:20px; }}</style></head><body>{body_html}</body></html>"
            
            ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            
            st.download_button(
                "📄 Download TXT",
                data=export_text,
                file_name=f"omnichat_export_{ts}.txt",
                mime="text/plain",
                use_container_width=True,
                key="btn_download_txt",
            )
            st.download_button(
                "📄 Download PDF",
                data=export_pdf,
                file_name=f"omnichat_export_{ts}.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="btn_download_pdf",
            )
            st.download_button(
                "📄 Download Markdown",
                data=md_content,
                file_name=f"omnichat_export_{ts}.md",
                mime="text/markdown",
                use_container_width=True,
                key="btn_download_md",
            )
            st.download_button(
                "📄 Download HTML",
                data=html_content,
                file_name=f"omnichat_export_{ts}.html",
                mime="text/html",
                use_container_width=True,
                key="btn_download_html",
            )
        else:
            st.info("No messages to export.")

# ---------------------------------------------------------------------------
# Main Chat Area — Mode-specific header
# ---------------------------------------------------------------------------
mode_descriptions = {
    "Dashboard": "Enterprise overview for conversations, knowledge, images, and sentiment.",
    "General Assistant": "💬 Ask me anything — I'm your general-purpose AI assistant.",
    "Knowledge Base Assistant": "📚 I'll answer questions using your uploaded documents.",
    "Knowledge Management": "Upload, delete, refresh, rebuild, and monitor knowledge-base documents.",
    "Medical Assistant": "🏥 Medical Q&A powered by NIH MedQuAD database.",
    "Research Assistant": "Search, summarize, cite, and explore computer-science research papers.",
    "Image Analysis": "🖼️ Upload an image and ask me to analyze it.",
    "Sentiment Analytics": "Track customer sentiment trends and confidence scores.",
    "Settings": "Manage profile, language, theme, API, and voice-ready architecture.",
}
st.markdown(
    f'<div class="mode-badge">{mode_icons.get(chat_mode, "🤖")} {chat_mode}</div>',
    unsafe_allow_html=True,
)
st.caption(mode_descriptions.get(chat_mode, ""))

if chat_mode == "Dashboard":
    render_dashboard_page()
    st.stop()
if chat_mode == "Knowledge Management":
    render_knowledge_management_page()
    st.stop()
if chat_mode == "Sentiment Analytics":
    render_sentiment_analytics_page()
    st.stop()
if chat_mode == "Settings":
    render_settings_page()
    st.stop()
if chat_mode == "Research Assistant":
    render_research_discovery_panel()

# Medical disclaimer (ONLY in Medical mode)
if chat_mode == "Medical Assistant":
    st.markdown(
        '<div class="medical-disclaimer">'
        '⚠️ <strong>Disclaimer:</strong> This chatbot is for educational purposes only and is not a substitute '
        'for professional medical advice, diagnosis, or treatment. Always consult a healthcare professional.'
        '</div>',
        unsafe_allow_html=True,
    )

def handle_image_generation_ui(original_prompt: str):
    """
    Renders progress, handles preview checking, runs prompt optimization,
    generates the image, and appends to the session state message history.
    """
    from image_pipeline.entities import extract_entities
    from image_pipeline.optimizer import optimize_prompt
    
    # Check keys
    gemini_key = None
    try:
        gemini_key = get_api_key()
    except Exception:
        pass
        
    openai_key = st.session_state.get("openai_api_key") or os.environ.get("OPENAI_API_KEY")
    
    # Style, ar, provider, quality overrides
    style_override = st.session_state.get("img_style_override") or "Auto"
    if style_override == "Auto":
        style_override = None
        
    ar_override = st.session_state.get("img_ar_override") or "Auto"
    if ar_override == "Auto":
        ar_override = None
        
    provider_override = st.session_state.get("img_provider_override") or "Auto"
    quality_override = st.session_state.get("img_quality_override") or "Standard"
    
    # 1. Run optimization first
    entities = extract_entities(original_prompt, api_key=gemini_key)
    optimized, meta = optimize_prompt(
        original_prompt,
        entities,
        style_override=style_override,
        aspect_ratio_override=ar_override
    )
    
    # If preview is enabled and not already approved
    if st.session_state.get("img_preview_enabled") and not st.session_state.get("approved_image_gen"):
        st.session_state.pending_image_gen = {
            "original_prompt": original_prompt,
            "optimized_prompt": optimized,
            "entities": entities,
            "metadata": meta,
            "style": meta["style"],
            "aspect_ratio": meta["aspect_ratio"],
            "provider": provider_override if provider_override != "Auto" else "Auto (Best Available)",
            "quality": quality_override
        }
        st.rerun()
        
    if st.session_state.get("approved_image_gen"):
        st.session_state.approved_image_gen = False
        
    progress_placeholder = st.empty()
    progress_placeholder.info("🎨 Enterprise Image Generation Pipeline active...")
    
    try:
        from image_pipeline.pipeline import run_pipeline
        
        est_sec = 25 if (provider_override and "OpenAI" in provider_override) or provider_override == "Auto" else 15
        progress_placeholder.info(f"⏳ Running generation pipeline (Estimated time: {est_sec}s)...")
        
        bypass = False
        if st.session_state.get("bypass_cache_once"):
            bypass = True
            st.session_state.bypass_cache_once = False

        result = run_pipeline(
            prompt=original_prompt,
            gemini_key=gemini_key,
            openai_key=openai_key,
            style_override=style_override,
            aspect_ratio_override=ar_override,
            provider_override=provider_override,
            quality_override=quality_override,
            bypass_cache=bypass,
            allow_placeholder=False
        )
        
        progress_placeholder.empty()
        
        if not result["success"]:
            progress_placeholder.error(f"⚠️ Image generation failed: {result['error']}")
            st.session_state.messages.append({
                "role": "assistant",
                "content": f"❌ **Image generation failed:** {result['error']}",
                "failed_prompt": original_prompt,
            })
            save_current_chat_session()
            st.rerun()
            
        if result.get("is_placeholder"):
            response_text = "⚠️ **Fallback placeholder generated.** (All online AI providers failed or were rate-limited)"
        else:
            response_text = "✨ **Image successfully generated!**"
        
        st.session_state.messages.append({
            "role": "assistant",
            "content": response_text,
            "image_path": result["image_path"],
            "original_prompt": original_prompt,
            "enhanced_prompt": result["enhanced_prompt"],
            "metadata": result["metadata"],
            "provider": result["provider"],
            "generation_time": result["generation_time_sec"],
            "is_placeholder": result.get("is_placeholder", False)
        })
        st.session_state.gemini_history.append(
            {"role": "model", "parts": [{"text": response_text}]}
        )
        save_current_chat_session()
        st.rerun()
    except Exception as e:
        progress_placeholder.error(f"⚠️ Image generation failed: {e}")
        st.session_state.messages.append({
            "role": "assistant",
            "content": f"❌ **Image generation failed:** {e}",
            "failed_prompt": original_prompt,
        })
        save_current_chat_session()
        st.rerun()

# ---------------------------------------------------------------------------
# Display existing chat history
# ---------------------------------------------------------------------------
for idx, msg in enumerate(st.session_state.messages):
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"], unsafe_allow_html=True)
        if msg.get("role") == "user" and msg.get("sentiment"):
            st.markdown(sentiment_badge_html(msg["sentiment"]), unsafe_allow_html=True)
        if msg.get("language"):
            lang_name = SUPPORTED_LANGUAGES.get(msg["language"], msg["language"])
            st.caption(f"Language: {lang_name}")
        
        # Enhanced image generation assistant blocks
        if "image_path" in msg and msg["image_path"]:
            st.markdown(f"**Original Prompt:** `{msg.get('original_prompt', '')}`")
            if msg.get("is_placeholder"):
                st.warning("⚠️ **Fallback placeholder generated.** (All online AI providers failed or were rate-limited)")
            
            enhanced = msg.get("enhanced_prompt")
            if enhanced:
                with st.expander("✨ View Enhanced Prompt Details"):
                    st.code(enhanced, wrap_lines=True)
                    if "metadata" in msg and msg["metadata"]:
                        st.json(msg["metadata"])
                    if "provider" in msg:
                        st.markdown(f"**Provider Model:** `{msg['provider']}` | **Time:** `{msg.get('generation_time', 0.0)}s`")
            
            st.image(msg["image_path"], caption=msg.get("original_prompt", "Generated Image"), use_container_width=True)
            
            # Action Buttons: Download PNG, Download JPG, Open, Regenerate, Upscale
            col_png, col_jpg, col_open, col_regen, col_upscale = st.columns(5)
            with col_png:
                try:
                    with open(msg["image_path"], "rb") as f:
                        png_bytes = f.read()
                    st.download_button(
                        "📥 PNG",
                        data=png_bytes,
                        file_name=os.path.basename(msg["image_path"]),
                        mime="image/png",
                        key=f"dl_png_{idx}",
                    )
                except Exception:
                    st.caption("File missing")
            with col_jpg:
                try:
                    import io
                    img_pil = Image.open(msg["image_path"])
                    if img_pil.mode in ("RGBA", "LA"):
                        img_pil = img_pil.convert("RGB")
                    buf = io.BytesIO()
                    img_pil.save(buf, format="JPEG", quality=90)
                    jpg_bytes = buf.getvalue()
                    st.download_button(
                        "📥 JPG",
                        data=jpg_bytes,
                        file_name=os.path.basename(msg["image_path"]).replace(".png", ".jpg"),
                        mime="image/jpeg",
                        key=f"dl_jpg_{idx}",
                    )
                except Exception:
                    st.caption("Convert failed")
            with col_open:
                try:
                    import base64
                    with open(msg["image_path"], "rb") as f:
                        b64_data = base64.b64encode(f.read()).decode("utf-8")
                    btn_html = (
                        f'<a href="data:image/png;base64,{b64_data}" target="_blank" download="{os.path.basename(msg["image_path"])}"'
                        f' style="display:inline-block; width:100%; padding: 0.35em 0px; border-radius: 4px;'
                        f' border: 1px solid #4B3F72; text-decoration: none; color: #FFF; background-color: #2D1B4E;'
                        f' text-align: center; font-size: 14px; box-sizing: border-box; line-height: 1.2;">🔓 Open</a>'
                    )
                    st.markdown(btn_html, unsafe_allow_html=True)
                except Exception:
                    st.caption("Open failed")
            with col_regen:
                if st.button("🔄 Regen", key=f"regen_{idx}", use_container_width=True):
                    st.session_state.regenerate_prompt = msg.get("original_prompt")
                    st.session_state.bypass_cache_once = True
                    st.rerun()
            with col_upscale:
                is_upscaled = msg["image_path"].endswith("_upscaled.png") or (msg.get("metadata") and msg["metadata"].get("is_upscaled"))
                if is_upscaled:
                    st.button("🔍 2x", key=f"upscale_{idx}", disabled=True, use_container_width=True)
                else:
                    if st.button("🔍 Upscale", key=f"upscale_{idx}", use_container_width=True):
                        try:
                            img_path = msg["image_path"]
                            from PIL import Image as PILImage
                            orig_img = PILImage.open(img_path)
                            w, h = orig_img.size
                            new_w, new_h = w * 2, h * 2
                            upscaled = orig_img.resize((new_w, new_h), PILImage.Resampling.LANCZOS)
                            
                            dir_name, file_name = os.path.split(img_path)
                            base_name, ext = os.path.splitext(file_name)
                            new_filename = f"{base_name}_upscaled.png"
                            new_path = os.path.join(dir_name, new_filename)
                            
                            upscaled.save(new_path, "PNG")
                            
                            # Update message states
                            msg["image_path"] = new_path
                            msg["content"] = "✨ **Image successfully upscaled to 2x resolution!**"
                            if "metadata" not in msg or not msg["metadata"]:
                                msg["metadata"] = {}
                            msg["metadata"]["resolution"] = f"{new_w}x{new_h}"
                            msg["metadata"]["is_upscaled"] = True
                            
                            try:
                                from database.storage import execute
                                execute("UPDATE generated_images_history SET filepath = ? WHERE filepath = ?", (new_path, img_path))
                            except Exception as dberr:
                                print(f"[Upscale DB Update Error] {dberr}", file=sys.stderr)
                                
                            st.rerun()
                        except Exception as ups_err:
                            st.error(f"Upscale failed: {ups_err}")

            # Expandable Section for Copying Prompt & Filepath
            with st.expander("📋 Copy Image Details"):
                st.caption("Copy Image Filepath:")
                st.code(msg["image_path"], language="text")
                st.caption("Copy Original Prompt:")
                st.code(msg.get("original_prompt", ""), language="text")

        if "failed_prompt" in msg and msg["failed_prompt"]:
            if st.button("🔄 Retry Generation", key=f"retry_{idx}"):
                st.session_state.regenerate_prompt = msg["failed_prompt"]
                st.session_state.messages.remove(msg)
                st.rerun()

        # Show medical entities expander (only for assistant messages in Medical mode)
        if msg["role"] == "assistant" and chat_mode == "Medical Assistant":
            entities = msg.get("entities")
            if entities and not entities.get("unavailable"):
                has_entities = any(entities.get(cat) for cat in ["SYMPTOM", "DISEASE", "TREATMENT", "MEDICATION", "BODY_PART"])
                if has_entities:
                    with st.expander("🔬 Detected Medical Entities"):
                        for cat in ["SYMPTOM", "DISEASE", "TREATMENT", "MEDICATION", "BODY_PART"]:
                            items = entities.get(cat, [])
                            if items:
                                st.markdown(f"**{cat.replace('_', ' ').title()}:** {', '.join(items)}")

# ---------------------------------------------------------------------------
# Prompt Preview (Step 9)
# ---------------------------------------------------------------------------
if st.session_state.get("pending_image_gen"):
    pending = st.session_state.pending_image_gen
    with st.chat_message("assistant"):
        st.info("💡 **Enterprise Prompt Preview & Analysis**")
        st.markdown(f"**Original Intent:** `{pending['original_prompt']}`")
        st.markdown(f"**AI-Enhanced Prompt:**")
        st.code(pending["optimized_prompt"], wrap_lines=True)
        
        entity_strs = [f"{e['name']} ({e['category']})" for e in pending.get("entities", [])]
        st.markdown(f"**Detected Entities:** {', '.join(entity_strs) or 'None'}")
        
        st.markdown(
            f"**Execution Settings:**\n"
            f"- Model Provider: `{pending['provider']}`\n"
            f"- Aspect Ratio: `{pending['aspect_ratio']}`\n"
            f"- Quality: `{pending['quality']}`\n"
            f"- Negative Prompt: `{pending['metadata']['negative_prompt']}`"
        )
        
        col_gen, col_cancel = st.columns(2)
        with col_gen:
            if st.button("🚀 Proceed to Generate", key="btn_proceed_gen"):
                st.session_state.approved_image_gen = True
                st.session_state.pending_image_gen = None
                handle_image_generation_ui(pending["original_prompt"])
        with col_cancel:
            if st.button("❌ Cancel", key="btn_cancel_gen"):
                st.session_state.pending_image_gen = None
                st.rerun()

# ---------------------------------------------------------------------------
# Image uploader (ONLY in Image Analysis mode)
# ---------------------------------------------------------------------------
if chat_mode == "Image Analysis":
    uploaded_images = st.file_uploader(
        "Upload images for analysis",
        type=["png", "jpg", "jpeg", "webp", "gif"],
        key="image_uploader",
        accept_multiple_files=True,
    )
    if uploaded_images:
        signature = [(file.name, getattr(file, "size", len(file.getvalue()))) for file in uploaded_images]
        if signature != st.session_state.get("image_upload_signature", []):
            records = []
            for uploaded in uploaded_images:
                file_bytes = uploaded.getvalue()
                record = save_uploaded_image_event(
                    file_bytes=file_bytes,
                    filename=uploaded.name,
                    user_id=get_active_user_id(),
                    session_id=st.session_state.active_session_id,
                )
                records.append(record)
            st.session_state.image_records = records
            st.session_state.temp_images = [record["image"] for record in records]
            st.session_state.image_upload_signature = signature

        for record in st.session_state.get("image_records", []):
            st.image(
                record["image"],
                caption=f"{record['filename']} ({record['width']}x{record['height']})",
                use_container_width=True,
            )
            if record.get("ocr_text"):
                with st.expander(f"OCR text: {record['filename']}"):
                    st.write(record["ocr_text"])

# ---------------------------------------------------------------------------
# Chat input
# ---------------------------------------------------------------------------
user_input = st.chat_input(f"Message {chat_mode}...")
if st.session_state.get("regenerate_prompt"):
    user_input = st.session_state.regenerate_prompt
    st.session_state.regenerate_prompt = None

if user_input:
    t_start = datetime.datetime.now()
    chat_logger.info(f"User Message: {user_input[:200]}... | Mode: {chat_mode}")
    api_logger.info(f"API Request initiated. Mode: {chat_mode}")
    language_context = prepare_language_context(user_input, st.session_state.get("language_selector", "auto"))
    st.session_state.last_language_context = language_context
    st.session_state.fallback_language = language_context.get("target_language", "en")
    query_text = language_context.get("english_text") or user_input
    model_user_message = build_model_user_message(language_context)
    sentiment = analyze_sentiment(user_input)
    st.session_state.latest_sentiment = sentiment
    record_sentiment(
        get_active_user_id(),
        st.session_state.active_session_id,
        user_input,
        sentiment,
    )

    # Display user message
    with st.chat_message("user"):
        st.markdown(user_input)
        st.markdown(sentiment_badge_html(sentiment), unsafe_allow_html=True)

    # Save user message
    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_input,
            "sentiment": sentiment,
            "language": language_context.get("detected_language", "en"),
        }
    )
    st.session_state.gemini_history.append(
        {"role": "user", "parts": [{"text": english_input}]}
    )

    # ---- ROUTE BASED ON MODE ----
    with st.chat_message("assistant"):
        response_text = ""
        entities_data = None

        try:
            # === DATE/TIME CHECK (all modes) ===
            if is_datetime_query(user_input) or is_datetime_query(query_text):
                response_text = get_datetime_response()
                st.markdown(response_text)

            # =================================================================
            # GENERAL ASSISTANT MODE
            # =================================================================
            elif chat_mode == "General Assistant":
                if is_realtime_query(query_text):
                    stream = None
                    fallback_text = None
                    with st.spinner("Searching live sources..."):
                        try:
                            stream, fallback_text = answer_live_query(query_text)
                        except Exception as e:
                            print(f"[Live Search Error] {e}", file=sys.stderr)
                            fallback_text = (
                                "I could not retrieve live information for that request. "
                                f"Reason: {e}"
                            )
                    if stream is not None:
                        response_text = render_streamed_response(stream)
                    else:
                        st.markdown(fallback_text)
                        response_text = fallback_text
                elif is_image_gen_query(user_input) or is_image_gen_query(query_text):
                    handle_image_generation_ui(user_input)
                else:
                    stream = None
                    first_chunk = None
                    iterator = None
                    with st.spinner("Thinking..."):
                        try:
                            # Stream response from Gemini
                            stream = send_message_stream(
                                history=st.session_state.gemini_history[:-1],
                                user_message=model_user_message,
                                system_instruction=build_enterprise_system_prompt(
                                    GENERAL_SYSTEM_PROMPT,
                                    sentiment,
                                    language_context,
                                ),
                            )
                            iterator = iter(stream)
                            first_chunk = next(iterator, None)
                        except (GeminiQuotaError, RuntimeError, Exception) as e:
                            print(f"[General Assistant Error] {e}", file=sys.stderr)
                            response_text = handle_local_fallback(user_input)
                            st.markdown(response_text)
                    if iterator is not None:
                        def stream_iterator():
                            if first_chunk is not None:
                                yield first_chunk
                            for chunk in iterator:
                                yield chunk
                        response_text = render_streamed_response(stream_iterator())

            # =================================================================
            # KNOWLEDGE BASE ASSISTANT MODE
            # =================================================================
            elif chat_mode == "Knowledge Base Assistant":
                stream = None
                chunks = None
                fallback_text = None
                first_chunk = None
                iterator = None
                with st.spinner("Searching documents..."):
                    # Skip RAG for greetings
                    if is_general_conversation(query_text):
                        try:
                            stream = send_message_stream(
                                history=st.session_state.gemini_history[:-1],
                                user_message=model_user_message,
                                system_instruction=build_enterprise_system_prompt(
                                    GENERAL_SYSTEM_PROMPT,
                                    sentiment,
                                    language_context,
                                ),
                            )
                            iterator = iter(stream)
                            first_chunk = next(iterator, None)
                        except (GeminiQuotaError, RuntimeError, Exception) as e:
                            fallback_text = handle_local_fallback(user_input)
                    else:
                        # Query FAISS for document chunks
                        chunks = query_relevant_chunks(query_text, k=3)
                        context_str = format_rag_context(chunks)
                        system_prompt = build_system_prompt_with_context(context_str)

                        try:
                            stream = send_message_stream(
                                history=st.session_state.gemini_history[:-1],
                                user_message=model_user_message,
                                system_instruction=build_enterprise_system_prompt(
                                    system_prompt,
                                    sentiment,
                                    language_context,
                                ),
                            )
                            iterator = iter(stream)
                            first_chunk = next(iterator, None)
                        except (GeminiQuotaError, RuntimeError, Exception) as e:
                            print(f"[KB Assistant Error] {e}", file=sys.stderr)
                            # Show retrieved chunks as fallback
                            if chunks:
                                fallback_text = "⚠️ **Gemini API unavailable.** Here are relevant excerpts from your documents:\n\n"
                                for i, chunk in enumerate(chunks):
                                    fallback_text += f"**📄 Source: {chunk['source']}**\n{chunk['content']}\n\n"
                            else:
                                fallback_text = handle_local_fallback(user_input)

                if iterator is not None:
                    def stream_iterator():
                        if first_chunk is not None:
                            yield first_chunk
                        for chunk in iterator:
                            yield chunk
                    response_text = render_streamed_response(stream_iterator())
                else:
                    st.markdown(fallback_text)
                    response_text = fallback_text

                # Show sources
                if chunks:
                    with st.expander("📎 Sources"):
                        for i, chunk in enumerate(chunks):
                            st.markdown(f"**[{i+1}]** {chunk['source']} (score: {chunk['score']:.3f})")

            # =================================================================
            # MEDICAL ASSISTANT MODE
            # =================================================================
            elif chat_mode == "Medical Assistant":
                sources = []
                response_generator = None
                first_chunk = None
                iterator = None
                fallback_text = None
                with st.spinner("Consulting medical database..."):
                    from medical_bot import send_medical_message_stream, DISCLAIMER_TEXT
                    from medical_retriever import query_medical_db
                    from medical_entities import detect_medical_entities, highlight_medical_entities

                    # Pre-fetch medical sources
                    if not is_general_conversation(query_text):
                        entities_dict = detect_medical_entities(query_text)
                        detected_entities = []
                        for cat, terms in entities_dict.items():
                            if cat != "unavailable":
                                detected_entities.extend(terms)
                        entities_tuple = tuple(sorted(list(set(detected_entities))))
                        sources = query_medical_db(query_text, entities=entities_tuple, k=5)

                    try:
                        response_generator, sources = send_medical_message_stream(
                            history=st.session_state.gemini_history[:-1],
                            user_message=model_user_message,
                            sources=sources,
                        )
                        iterator = iter(response_generator)
                        first_chunk = next(iterator, None)
                    except (GeminiQuotaError, RuntimeError, Exception) as e:
                        print(f"[Medical Assistant Error] {e}", file=sys.stderr)
                        # Fallback: show MedQuAD results directly
                        if sources:
                            fallback_text = "⚠️ **Gemini API unavailable.** Here are results from the MedQuAD database:\n\n"
                            for idx, src in enumerate(sources):
                                fallback_text += (
                                    f"### Medical Record {idx + 1}: {src.get('focus', 'General')}\n"
                                    f"- **Question:** {src.get('focus', '')}\n"
                                    f"- **Answer:** {src.get('answer', '')}\n"
                                    f"- **Source:** *{src.get('source', 'MedQuAD')}*\n\n"
                                )
                        else:
                            fallback_text = handle_local_fallback(user_input)

                if iterator is not None:
                    def stream_iterator():
                        if first_chunk is not None:
                            yield first_chunk
                        for chunk in iterator:
                            yield chunk
                    response_text = render_streamed_response(stream_iterator())
                else:
                    st.markdown(fallback_text)
                    response_text = fallback_text

                # Detect medical entities
                try:
                    entities_data = detect_medical_entities(response_text)
                except Exception:
                    entities_data = None

                # Show medical sources
                if sources:
                    with st.expander(f"📋 Medical Sources ({len(sources)} records)"):
                        for idx, src in enumerate(sources):
                            confidence = int(src.get("similarity", 0) * 100)
                            st.markdown(
                                f"**[{idx+1}]** {src.get('focus', 'N/A')} — "
                                f"*{src.get('source', 'MedQuAD')}* "
                                f"(Confidence: {confidence}%)"
                            )

                # Show entities
                if entities_data and not entities_data.get("unavailable"):
                    has_entities = any(entities_data.get(cat) for cat in ["SYMPTOM", "DISEASE", "TREATMENT", "MEDICATION", "BODY_PART"])
                    if has_entities:
                        with st.expander("🔬 Detected Medical Entities"):
                            for cat in ["SYMPTOM", "DISEASE", "TREATMENT", "MEDICATION", "BODY_PART"]:
                                items = entities_data.get(cat, [])
                                if items:
                                    st.markdown(f"**{cat.replace('_', ' ').title()}:** {', '.join(items)}")

                # Disclaimer
                st.caption(DISCLAIMER_TEXT)

            # =================================================================
            # RESEARCH ASSISTANT MODE
            # =================================================================
            elif chat_mode == "Research Assistant":
                papers = []
                stream = None
                first_chunk = None
                iterator = None
                fallback_text = None
                with st.spinner("Searching CS papers..."):
                    papers = search_papers(
                        query_text,
                        max_results=8,
                        include_live_arxiv=st.session_state.get("research_live_arxiv", True),
                    )
                    st.session_state["research_last_results"] = papers
                    record_research_query(get_active_user_id(), query_text, len(papers))
                    paper_context = format_papers_for_prompt(papers)
                    research_prompt = (
                        f"{RESEARCH_SYSTEM_PROMPT}\n\n"
                        "Use this paper context for search, summarization, related work, and citations.\n\n"
                        f"{paper_context}"
                    )
                    try:
                        stream = send_message_stream(
                            history=st.session_state.gemini_history[:-1],
                            user_message=model_user_message,
                            system_instruction=build_enterprise_system_prompt(
                                research_prompt,
                                sentiment,
                                language_context,
                            ),
                            max_output_tokens=4096,
                        )
                        iterator = iter(stream)
                        first_chunk = next(iterator, None)
                    except (GeminiQuotaError, RuntimeError, Exception) as e:
                        print(f"[Research Assistant Error] {e}", file=sys.stderr)
                        fallback_text = summarize_papers(papers)

                if iterator is not None:
                    def stream_iterator():
                        if first_chunk is not None:
                            yield first_chunk
                        for chunk in iterator:
                            yield chunk
                    response_text = render_streamed_response(stream_iterator())
                else:
                    st.markdown(fallback_text)
                    response_text = fallback_text

                if papers:
                    with st.expander("Research citations & PDF links"):
                        for idx, paper in enumerate(papers, 1):
                            abs_url = paper.get("url", "")
                            pdf_url = paper.get("pdf_url") or ""
                            if not pdf_url and "arxiv.org/abs/" in abs_url:
                                pdf_url = abs_url.replace("arxiv.org/abs/", "arxiv.org/pdf/") + ".pdf"
                            
                            pdf_md = f" | [PDF Link]({pdf_url})" if pdf_url else ""
                            st.markdown(
                                f"**[{idx}] {paper.get('title', 'Untitled')}** - "
                                f"{paper.get('authors', 'Unknown')} "
                                f"([Abstract Link]({abs_url}){pdf_md})"
                            )
                    related = related_papers(papers[0], papers)
                    if related:
                        with st.expander("Related papers"):
                            for paper in related:
                                st.markdown(f"- **{paper.get('title')}** ({paper.get('year', 'n.d.')})")

            # =================================================================
            # IMAGE ANALYSIS MODE
            # =================================================================
            elif chat_mode == "Image Analysis":
                if is_image_gen_query(user_input) or is_image_gen_query(query_text):
                    handle_image_generation_ui(user_input)
                else:
                    images = st.session_state.get("temp_images", [])
                    if not images:
                        response_text = "Please upload an image first using the file uploader above, then ask your question."
                        st.markdown(response_text)
                    else:
                        from multimodal.image_service import edit_image
                        last_img = images[-1]
                        
                        edited_img = None
                        status_msg = None
                        edit_res = None
                        with st.spinner("Editing image..."):
                            edit_res = edit_image(last_img, query_text)
                        
                        if edit_res is not None:
                            edited_img, status_msg = edit_res
                            try:
                                from image_generator import save_generated_image
                                filepath = save_generated_image(edited_img, f"edited_{query_text}")
                                response_text = f"🎨 **{status_msg}**"
                                st.markdown(response_text)
                                st.image(edited_img, caption="Edited Image", use_container_width=True)
                                
                                st.session_state.temp_images[-1] = edited_img
                                
                                st.session_state.messages.append({
                                    "role": "assistant",
                                    "content": response_text,
                                    "image_path": filepath
                                })
                                st.session_state.gemini_history.append(
                                    {"role": "model", "parts": [{"text": response_text}]}
                                )
                                save_current_chat_session()
                                response_text = None
                            except Exception as e:
                                response_text = f"⚠️ Image editing failed: {e}"
                                st.markdown(response_text)
                        else:
                            stream = None
                            first_chunk = None
                            iterator = None
                            fallback_text = None
                            with st.spinner("Analyzing image..."):
                                try:
                                    ocr_context = "\n\n".join(
                                        f"{record.get('filename')}: {record.get('ocr_text')}"
                                        for record in st.session_state.get("image_records", [])
                                        if record.get("ocr_text")
                                    )
                                    image_user_message = model_user_message
                                    if ocr_context:
                                        image_user_message += (
                                            "\n\nOCR text extracted from uploaded images:\n"
                                            f"{ocr_context}"
                                        )
                                    stream = send_message_stream(
                                        history=st.session_state.gemini_history[:-1],
                                        user_message=image_user_message,
                                        system_instruction=build_enterprise_system_prompt(
                                            IMAGE_ANALYSIS_SYSTEM_PROMPT,
                                            sentiment,
                                            language_context,
                                        ) + "\n\nInstructions:\n"
                                        "If the user asks to summarize, caption, classify, compare, or answer questions about the image(s), "
                                        "use your vision capability to analyze the image(s) and provide the requested details.",
                                        images=images,
                                    )
                                    iterator = iter(stream)
                                    first_chunk = next(iterator, None)
                                except (GeminiQuotaError, RuntimeError, Exception) as e:
                                    print(f"[Image Analysis Error] {e}", file=sys.stderr)
                                    fallback_text = "⚠️ **Gemini API unavailable.** Image analysis requires an active API connection. Please check your API key in Settings."

                            if iterator is not None:
                                def stream_iterator():
                                    if first_chunk is not None:
                                        yield first_chunk
                                    for chunk in iterator:
                                        yield chunk
                                response_text = render_streamed_response(stream_iterator())
                            else:
                                st.markdown(fallback_text)
                                response_text = fallback_text

        except Exception as e:
            # Catch-all safety net
            print(f"[Outer Exception] {e}", file=sys.stderr)
            response_text = handle_local_fallback(user_input)
            st.markdown(response_text)

        # ---- Save assistant response to session state ----
        if response_text is not None:
            msg_data = {"role": "assistant", "content": response_text}
            if entities_data:
                msg_data["entities"] = entities_data
            st.session_state.messages.append(msg_data)
            st.session_state.gemini_history.append(
                {"role": "model", "parts": [{"text": response_text}]}
            )
            save_current_chat_session()

        # Task 11 logging
        if "t_start" in locals():
            duration_ms = (datetime.datetime.now() - t_start).total_seconds() * 1000
            perf_logger.info(f"Response duration: {duration_ms:.2f}ms | Mode: {chat_mode}")
            if response_text:
                chat_logger.info(f"Assistant Response: {response_text[:200]}...")
                api_logger.info("API Response received successfully.")
            else:
                chat_logger.warning("Empty response received from Assistant.")
                api_logger.warning("Empty API Response returned.")

        # Show model info
        model_used = st.session_state.get("active_model_used", "")
        if model_used and response_text and not response_text.startswith("⚠️"):
            now_str = datetime.datetime.now().strftime("%I:%M %p")
            st.caption(f"🤖 {model_used} • {now_str}")
