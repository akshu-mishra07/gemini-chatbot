# Codebase Concerns

**Analysis Date:** 2026-07-01

## Tech Debt

**Monolithic Presentation File:**
- Issue: [app.py](file:///c:/Users/ACER/OneDrive/Desktop/gemini-chatbot/streamlit-chatbot/app.py) is over 1600 lines (70 KB), containing CSS injection, route management, view rendering for 10 screens, live weather parsing, state initialization, and local fallbacks.
- Why: Rapid integration of multiple modes and modular services without splitting presentation files.
- Impact: Hard to maintain, high risk of regression when editing single pages, and difficult to test views in isolation.
- Fix approach: Refactor `app.py` views into individual modules under a `views/` folder (e.g., `views/dashboard.py`, `views/settings.py`).

**Root Workspace Clutter:**
- Issue: 20+ recovery and temporary Python scripts clutter the main app directory (e.g., `recovered_globals.py`, `merge_reconstructed.py`, `smart_reconstruct.py`, `inspect_step_2610.py`, etc.).
- Why: Leftover files from code disassembly recovery sessions.
- Impact: Confuses new developers and complicates file searches.
- Fix approach: Move all helper scripts to an `archive/` or `scratch/` folder.

## Security Considerations

**API Key Storage:**
- Risk: Session state stores user API keys, and developers could accidentally commit local `.env` files with credentials.
- Current mitigation: `.env` is listed in `.gitignore` (if configured), and sidebar checks for keys dynamically.
- Recommendations: Add a validation check in a git hook to block committing `.env`, and use environment variables rather than UI configuration where possible.

**User Registration Password Hashing:**
- Risk: Password storage security depends on the robustness of the hashing implemented in `auth/service.py`.
- Current mitigation: Custom local hashing.
- Recommendations: Ensure standard libraries (like `bcrypt` or `hashlib`'s pbkdf2) are used with adequate salt iterations.

## Performance Bottlenecks

**Local Transformers Model Loading:**
- Problem: Local model loading for `sentence-transformers` and `transformers` (sentiment) requires high memory and CPU time.
- Measurement: Can take 5–15 seconds to load models on startup, and causes high memory spikes (1-2 GB+).
- Cause: Downloading and running dense tensor models in-memory on CPU nodes.
- Improvement path: Lazy load models only when the respective page/action is accessed; offer API fallback (like Hugging Face Inference API) to offload local CPU execution.

**Blocking Main UI Thread:**
- Problem: Running document chunking and FAISS database index rebuilding runs on Streamlit's main execution loop.
- Cause: Synchronous processing of large documents.
- Impact: UI freezes or shows loading indicators for up to several minutes during heavy PDF uploads.
- Improvement path: Offload vector database builds and folder watching to a background thread or process.

## Fragile Areas

**OCR Binary System Dependencies:**
- Files: [document_processor.py](file:///c:/Users/ACER/OneDrive/Desktop/gemini-chatbot/streamlit-chatbot/document_processor.py)
- Why fragile: Relies on `pytesseract` and `pdf2image` which call underlying system binaries `tesseract` and `pdftoppm` (Poppler).
- Common failures: App crashes or silent omissions of text when running on servers that don't have these system binaries installed.
- Safe modification: Wrap binary calls in check/try-catch logic, and show a clear UI warning if system binaries are missing.

**SQLite Concurrency:**
- Files: [database/storage.py](file:///c:/Users/ACER/OneDrive/Desktop/gemini-chatbot/streamlit-chatbot/database/storage.py)
- Why fragile: SQLite locks the database file on writes.
- Common failures: Multiple users interacting with the chatbot simultaneously can cause `sqlite3.OperationalError: database is locked`.
- Safe modification: Configure SQLite timeout flags to allow retries, or migrate to a PostgreSQL instance for multi-user production.

## Test Coverage Gaps

**Lack of Unit Tests:**
- What's not tested: Almost all service layer functions (auth hashing, multilingual translations, RAG retrieval scoring, chatbot routing).
- Risk: Changes in database helper schemas or RAG prompts can break core functions unnoticed.
- Priority: High.
- Difficulty to test: Need to mock SQLite connections and Gemini API responses.

---

*Concerns audit: 2026-07-01*
*Update as issues are fixed or new ones discovered*
