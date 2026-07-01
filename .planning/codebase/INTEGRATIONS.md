# External Integrations

**Analysis Date:** 2026-07-01

## APIs & External Services

**AI Inference & LLM:**
- Google Gemini API - Core text generation, streaming, fallback, and multimodal Vision analysis.
  - SDK/Client: `google-genai` Python library.
  - Auth: API key in `GEMINI_API_KEY` environment variable or UI settings inputs.
  - Endpoints/Models: Gemini Pro, Gemini Flash models.

**Image Generation:**
- Gemini Imagen / Hugging Face / Pollinations - Generates images from text descriptions.
  - Integration method: HTTP requests or SDK calls.
  - Auth: `GEMINI_API_KEY` for Imagen, `HF_TOKEN` for Hugging Face, no auth for Pollinations.
  - Trigger: Auto-detected in user message (e.g., "draw a picture of...") or explicit prompt.

**Computer Science Research:**
- arXiv REST API - Retrieves research papers, details, and metadata.
  - Integration method: HTTP GET requests to `http://export.arxiv.org/api/query`.
  - Auth: None (public endpoint).
  - Fallback: Local CS papers database if offline or API fails.

**Web Search & Weather:**
- Public Web Search / Open-Meteo Weather API - Retrieves weather metrics and search summaries for live queries.
  - Integration method: Web scraping and REST APIs via `requests`.
  - Auth: None (public endpoints / scraping).

**Translation Services:**
- deep-translator API - Provides multilingual translation.
  - SDK/Client: `deep-translator` library.
  - Auth: None (public translation API hooks).

## Data Storage

**Databases:**
- SQLite (Local File) - Stores users, profiles, chat session lists, sentiment events, and multimodal OCR logs.
  - Connection: Local file path specified in `OMNICHAT_DB_PATH` (defaults to `database/omnichat.db`).
  - Client: Python standard `sqlite3` library.
  - Schema initialization: Managed via `database/storage.py:initialize_database()`.

**Vector Stores:**
- FAISS Index (Local Files) - Stores document embeddings for semantic search.
  - Connection: Filesystem paths:
    - User KB: `vector_store/faiss_index`
    - Medical DB: `vector_store/medical_faiss_index`
  - Client: `faiss-cpu` library.
  - Embeddings: Generated using `sentence-transformers` locally.

**File Storage:**
- Local Disk - Uploaded documents (`vector_store/documents/`) and generated images (`generated_images/`).

## Authentication & Identity

**Auth Provider:**
- Custom Local SQLite Auth - User password validation and profile storage.
  - Implementation: `auth/service.py` using hash comparisons.
  - Session management: In-memory Streamlit state `st.session_state.authenticated_user` and `st.session_state.user_profile`.

## Monitoring & Observability

**Logs:**
- stdout / stderr - Console outputs from Streamlit server.
- Database Tables - Sentiment history and multimodal OCR history stored in SQLite database.

## CI/CD & Deployment

**Hosting:**
- Runs on local host (`http://localhost:8501`) or standard VPS/Container deployment.
- Env configuration is resolved via `python-dotenv`.

## Environment Configuration

**Development:**
- Required env vars: `GEMINI_API_KEY`
- Mock/stub services: Local Python fallback handlers (e.g. `LOCAL_KNOWLEDGE_BASE`, `LOCAL_GREETINGS`) run automatically when the Gemini API fails or runs out of quota.

---

*Integration audit: 2026-07-01*
*Update when adding/removing external services*
