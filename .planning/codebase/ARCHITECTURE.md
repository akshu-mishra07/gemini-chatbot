# Architecture

**Analysis Date:** 2026-07-01

## Pattern Overview

**Overall:** Streamlit Web Application with Service-Oriented Modules.

**Key Characteristics:**
- **Single-page Streamlit Interface:** User views are rendered as a single page with sidebar navigation routing among 10 distinct modes/pages.
- **State-driven routing:** Navigation is driven entirely by Streamlit session state (`st.session_state.chat_mode`), triggering isolated code paths.
- **Service Isolation:** Logic is divided into distinct Python modules (`research`, `sentiment`, `auth`, `database`, `multilingual`, `multimodal`), minimizing dependencies between components.
- **Local SQLite & Filesystem Persistence:** User profiles, sessions, and vector databases run entirely on the local system.

## Layers

**View/Presentation Layer (`streamlit-chatbot/app.py`):**
- Purpose: Render the SaaS interface, handle user input, render chat sessions, inject custom dark purple/light theme CSS overrides, and display dashboards.
- Contains: Streamlit widgets, layout columns, pages view logic.
- Used by: End user via browser.

**Routing / Orchestration Layer (`streamlit-chatbot/app.py`):**
- Purpose: Initialize session state, clear mode-specific caches on switch, route user input to appropriate backend services.
- Contains: Navigation selections, mode switch handler, prompt pre-processors.
- Depends on: View Layer and Service Layer.

**Service Layer (Individual module folders and files):**
- Purpose: Encapsulate core capabilities (LLM integration, search, databases, models, OCR).
- Contains:
  - `chatbot.py`: Gemini client connector, retry handler.
  - `chat_manager.py`: Serialization of session histories.
  - `knowledge_manager.py` / `vector_store.py` / `rag_engine.py`: Vector search index building, chunking, retrieval.
  - `auth/service.py`: Hashed SQLite auth.
  - `database/storage.py`: Local database connector.
  - `multilingual/service.py`: Translation client.
  - `multimodal/image_service.py`: Vision and OCR upload record helper.
  - `research/service.py`: arXiv metadata searcher.
  - `sentiment/service.py`: Transformers/lexical sentiment analyzer.
  - `medical_bot.py` / `medical_entities.py` / `medical_retriever.py` / `medical_vector_store.py`: MedQuAD search, entities, safety disclaimer injector.
- Depends on: Local database, FAISS indices, and external APIs.

**Data Storage / Persistence Layer:**
- Purpose: Physical storage of application state, files, and index nodes.
- Contains: SQLite file (`database/omnichat.db`), FAISS folders (`vector_store/faiss_index/`), uploaded documents (`vector_store/documents/`), and generated images (`generated_images/`).

## Data Flow

### 1. User Message Execution Flow (e.g., General Assistant Chat)
1. User enters text in `st.chat_input`.
2. `app.py` captures the input and appends the message to `st.session_state.messages`.
3. Pre-processors verify query intents:
   - Weather/search query? → Calls `web_search.py` and synthesizes context.
   - Date/time query? → Returns local date/time response directly.
   - Image generation query? → Triggers `image_generator.py` and renders image inline.
4. Sentiment is analyzed via `sentiment/service.py:analyze_sentiment()` and logged via `record_sentiment()`.
5. Language is detected and appropriate translation hooks are run via `multilingual/service.py`.
6. System prompt is constructed via `build_enterprise_system_prompt()`, appending sentiment guidelines and language policies.
7. Call is dispatched to `chatbot.py:send_message_stream()`.
8. Streamed chunks are rendered via `app.py:render_streamed_response()`.
9. The resulting chat session is written to SQLite via `save_current_chat_session()`.

### 2. Document Indexing Flow
1. User uploads files in `Knowledge Management` page.
2. `knowledge_manager.py:add_document()` stores the file locally.
3. `document_processor.py` extracts text (utilizing OCR if it's an image or scanned PDF) and splits it into semantic chunks.
4. Chunks are embedded via `sentence-transformers` and pushed to `vector_store.py`.
5. FAISS index is saved to disk under `vector_store/faiss_index/`.

## Key Abstractions

**Service Adapter:**
- Logic is exported as modules containing utility functions, rather than complex object hierarchies. Examples: `auth/service.py`, `sentiment/service.py`, `research/service.py`.

**Vector Store Connector:**
- `vector_store.py` encapsulates FAISS indexing, loading, and saving.
- `medical_vector_store.py` wraps the read-only MedQuAD indices.

**Gemini API Client:**
- `chatbot.py` encapsulates LLM connections, retry loops, and local fallback responses if quota errors occur.

## Entry Points

**Streamlit Web App Entry:**
- Location: `streamlit-chatbot/app.py`
- Triggers: Running command `streamlit run app.py`
- Responsibilities: Main UI layout, page navigation, sidebar session controls.

**Database Initializer:**
- Location: `streamlit-chatbot/database/storage.py`
- Triggers: Imported in `app.py` on load.
- Responsibilities: Verifies SQLite tables, creates them if missing, seeds default values.

## Error Handling

**Strategy:** Fail gracefully to local backups.
- **Gemini Fallback:** If the Gemini API fails (network offline or quota exceeded), `chatbot.py` catches `GeminiQuotaError` and uses the local Python dictionaries (`LOCAL_GREETINGS`, `LOCAL_KNOWLEDGE_BASE`) to serve responses offline.
- **Research Fallback:** If the arXiv API query fails, `research/service.py` falls back to search in a local CS paper corpus.
- **Sentiment Fallback:** If the Hugging Face sentiment model fails to download or load, the system falls back to a deterministic lexical lookup.

## Cross-Cutting Concerns

**Authentication:**
- Managed via `auth/service.py` checking SQLite users table. Checked on page rendering to display Guest vs Authenticated controls in the sidebar.

**Sentiment & Analytics:**
- User inputs are automatically audited for emotional tone, updating the Plotly metric dashboards.

**Multilingual Handling:**
- Automated detection and translation hooks run on both incoming prompts and outgoing chatbot replies.

---

*Architecture analysis: 2026-07-01*
*Update when major patterns change*
