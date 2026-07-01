# Technology Stack

**Analysis Date:** 2026-07-01

## Languages

**Primary:**
- Python 3.9+ - All application logic, service layer, and RAG processing code.

**Secondary:**
- HTML/CSS - Custom premium UI styling overrides injected inside `app.py` for Streamlit elements.

## Runtime

**Environment:**
- Python 3.9+ local or server runtime.
- Browser client accessing the Streamlit web server.

**Package Manager:**
- pip - Package installer for Python.
- Lockfile: None (uses `requirements.txt` only).

## Frameworks

**Core:**
- Streamlit >= 1.35.0 - Core web framework for dashboard, sidebar, session routing, and interactive chat interface.

**Testing:**
- None (manual execution and verification).

## Key Dependencies

**Critical:**
- `google-genai` - Official Google Gemini API SDK for text generation, streaming, fallback orchestration, and Vision processing.
- `faiss-cpu` - Local dense vector storage for semantic retrieval of uploaded documents and MedQuAD medical Q&A.
- `sentence-transformers` - Generates high-quality sentence embeddings for local document chunks.
- `transformers` - Sentiment analysis model execution (falls back to lexical if model cache missing).
- `spacy` - Entity recognition for medical terms (extracting diseases, drugs, etc. from query).

**Infrastructure:**
- `langchain` & `langchain-community` & `langchain-text-splitters` - Document processing, chunking, and metadata parsing.
- `python-dotenv` - Environment variable resolution from local `.env` files.
- `sqlite3` (Python Standard Library) - Database connection for user profiles, session storage, sentiment logs, and OCR history.
- `pytesseract` & `pdf2image` - Image OCR processing (requires system Tesseract OCR and Poppler binaries).
- `PyMuPDF` (fitz) & `python-docx` - Local PDF and Word document extraction.
- `deep-translator` & `langdetect` - Multilingual detection and translation hooks.
- `plotly` - Visual dashboard widgets for sentiment and chat analytics.
- `requests` - arXiv API querying and web search utilities.

## Configuration

**Environment:**
- Configured via `.env` file or environment variables.
- Critical keys:
  - `GEMINI_API_KEY` - Required Google Gemini API credential (can also be supplied in UI Settings).
  - `HF_TOKEN` / `HUGGINGFACE_API_KEY` - Optional key for Hugging Face image-generation fallback.
  - `OMNICHAT_DB_PATH` - Optional path for SQLite database (defaults to `database/omnichat.db`).

**Build:**
- `.streamlit/config.toml` - Streamlit server properties (port `8501`, address `0.0.0.0`, `headless=true`, CORS disabled).

## Platform Requirements

**Development:**
- Windows/macOS/Linux with Python 3.9+.
- Tesseract OCR (system binary) on PATH for image text extraction.
- Poppler (system binaries) on PATH for PDF page image conversion.

**Production:**
- Streamlit Community Cloud, Heroku, Docker on VPS/ECS, or similar Python server hosting.
- Requires persistent volume storage if local FAISS index or SQLite database is to be retained across redeployments.

---

*Stack analysis: 2026-07-01*
*Update after major dependency changes*
