# Codebase Structure

**Analysis Date:** 2026-07-01

## Directory Layout

```text
c:\Users\ACER\OneDrive\Desktop\gemini-chatbot/
  .agents/                      GSD Core configuration and runtime skills
    gsd-core/                   OpenGSD workflow engines and resources
    skills/                     OpenGSD command skills folder
  .venv/                        Python virtual environment (excluded from commits)
  docs/                         Screenshots and repository documentation
  medquad_data/                 MedQuAD dataset CSV/TXT files for medical search
  vector_store/                 FAISS indexes and uploaded raw documents
  generated_images/             Generated PNG files
  chat_sessions/                Exported chat transcripts (PDF/TXT)
  streamlit-chatbot/            Core Python Web Application
    .streamlit/                 Streamlit configuration files
    auth/                       Local user authentication service
    database/                   SQLite database persistence layers
    multilingual/               Language translation and policy adapters
    multimodal/                 Vision analysis OCR log services
    research/                   arXiv search and CS paper fallbacks
    sentiment/                  Sentiment classification and metrics persistence
```

## Key Files

### Configuration & Tooling
- [requirements.txt](file:///c:/Users/ACER/OneDrive/Desktop/gemini-chatbot/streamlit-chatbot/requirements.txt) - Python package dependencies list.
- [config.toml](file:///c:/Users/ACER/OneDrive/Desktop/gemini-chatbot/streamlit-chatbot/.streamlit/config.toml) - Headless address/port configurations for Streamlit.
- [.env](file:///c:/Users/ACER/OneDrive/Desktop/gemini-chatbot/streamlit-chatbot/.env) - Local credentials for Gemini/Hugging Face keys.

### Core Application
- [app.py](file:///c:/Users/ACER/OneDrive/Desktop/gemini-chatbot/streamlit-chatbot/app.py) - Main presentation UI shell, state initializer, and sidebar view router.
- [chatbot.py](file:///c:/Users/ACER/OneDrive/Desktop/gemini-chatbot/streamlit-chatbot/chatbot.py) - Gemini client connection wrapper with error recovery/local fallback hooks.
- [chat_manager.py](file:///c:/Users/ACER/OneDrive/Desktop/gemini-chatbot/streamlit-chatbot/chat_manager.py) - Exporters for chat sessions into PDF/TXT formats.
- [web_search.py](file:///c:/Users/ACER/OneDrive/Desktop/gemini-chatbot/streamlit-chatbot/web_search.py) - Live web-scraping search helper.
- [image_generator.py](file:///c:/Users/ACER/OneDrive/Desktop/gemini-chatbot/streamlit-chatbot/image_generator.py) - Fallback interface for text-to-image prompts.

### Knowledge Base & RAG
- [document_processor.py](file:///c:/Users/ACER/OneDrive/Desktop/gemini-chatbot/streamlit-chatbot/document_processor.py) - PDF/DOCX/CSV/TXT reader and text splitter.
- [vector_store.py](file:///c:/Users/ACER/OneDrive/Desktop/gemini-chatbot/streamlit-chatbot/vector_store.py) - Dense vector store index (FAISS-cpu) controller.
- [knowledge_manager.py](file:///c:/Users/ACER/OneDrive/Desktop/gemini-chatbot/streamlit-chatbot/knowledge_manager.py) - Folder watcher and vector rebuild scheduler.
- [rag_engine.py](file:///c:/Users/ACER/OneDrive/Desktop/gemini-chatbot/streamlit-chatbot/rag_engine.py) - Query context builder for Gemini prompts.

### Medical Q&A Subsystem
- [medical_bot.py](file:///c:/Users/ACER/OneDrive/Desktop/gemini-chatbot/streamlit-chatbot/medical_bot.py) - Prompt orchestrator and safety disclaimer formatter.
- [medical_entities.py](file:///c:/Users/ACER/OneDrive/Desktop/gemini-chatbot/streamlit-chatbot/medical_entities.py) - Named entity recognizer for clinical terms.
- [medical_retriever.py](file:///c:/Users/ACER/OneDrive/Desktop/gemini-chatbot/streamlit-chatbot/medical_retriever.py) - Retrieval scoring algorithm.
- [medical_vector_store.py](file:///c:/Users/ACER/OneDrive/Desktop/gemini-chatbot/streamlit-chatbot/medical_vector_store.py) - Parser and indexer for raw MedQuAD dataset files.

### Modular Service Folders
- [auth/service.py](file:///c:/Users/ACER/OneDrive/Desktop/gemini-chatbot/streamlit-chatbot/auth/service.py) - Handles sqlite-backed password hashing and profile checks.
- [database/storage.py](file:///c:/Users/ACER/OneDrive/Desktop/gemini-chatbot/streamlit-chatbot/database/storage.py) - Database creation, SQL execution helpers, and sessions table manager.
- [multilingual/service.py](file:///c:/Users/ACER/OneDrive/Desktop/gemini-chatbot/streamlit-chatbot/multilingual/service.py) - Automatically translates user inputs and system prompts based on target settings.
- [multimodal/image_service.py](file:///c:/Users/ACER/OneDrive/Desktop/gemini-chatbot/streamlit-chatbot/multimodal/image_service.py) - Visions OCR event persistence.
- [research/service.py](file:///c:/Users/ACER/OneDrive/Desktop/gemini-chatbot/streamlit-chatbot/research/service.py) - Connects arXiv API endpoints and visualizes result timelines.
- [sentiment/service.py](file:///c:/Users/ACER/OneDrive/Desktop/gemini-chatbot/streamlit-chatbot/sentiment/service.py) - Calculates positive/negative scores for analytics screens.

---

*Structure analysis: 2026-07-01*
*Update when files are added, moved, or deleted*
