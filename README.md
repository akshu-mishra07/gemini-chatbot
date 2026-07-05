# OmniChat AI Customer Service Platform

OmniChat AI is a Streamlit-based enterprise customer-service platform powered by Google Gemini, FAISS retrieval, MedQuAD medical search, multimodal image understanding, sentiment analytics, multilingual support, and research-paper assistance.

The project preserves the original Gemini chatbot, chat history, Streamlit UI, conversation memory, README, and requirements workflow while extending the app into a modular SaaS-style assistant.

## Core Features

- General Gemini assistant with streaming responses, model fallback, local fallback, live search helpers, chat history, and export.
- Dynamic knowledge base with PDF, DOCX, TXT, CSV, and image OCR ingestion, chunking, Sentence Transformer embeddings, FAISS indexing, semantic retrieval, citations, similarity scores, document deletion, watched folders, refresh, and rebuild.
- Multimodal assistant with multiple image uploads, preview, OCR extraction, persistent image history, Gemini Vision analysis, and optional image generation from text prompts.
- Medical Q&A powered by a MedQuAD FAISS index, medical entity extraction, confidence scores, source citations, and a safety disclaimer.
- Computer-science research assistant with arXiv search when network access is available, local CS fallback corpus, summarization, citations, related papers, keyword search, semantic-style ranking, and timeline visualization.
- Sentiment analysis for Positive, Negative, and Neutral messages with confidence scores, tone-aware responses, persisted sentiment history, and analytics dashboard.
- Multilingual workflow for English, Hindi, Marathi, and Spanish with automatic detection, translation hooks, response-language control, and voice-ready adapter configuration.
- Local authentication, user profiles, settings, dark/light theme controls, dashboard metrics, searchable chat sessions, conversation export, and clear conversation controls.

## Architecture

```text
streamlit-chatbot/
  app.py                         Streamlit shell, navigation, pages, and chat router
  chatbot.py                     Gemini API client, streaming, retries, model fallback
  chat_manager.py                Persistent chat sessions and TXT/PDF export
  document_processor.py          PDF/DOCX/TXT/CSV/image OCR extraction and chunking
  vector_store.py                Knowledge-base FAISS persistence
  knowledge_manager.py           Uploads, metadata, deletion, watched folders, refresh
  rag_engine.py                  Semantic search and RAG prompt assembly
  medical_vector_store.py        MedQuAD parsing and FAISS build
  medical_retriever.py           Medical retrieval and confidence scoring
  medical_entities.py            Medical entity recognition
  medical_bot.py                 Medical safety prompt and response orchestration
  image_generator.py             Gemini Imagen, Hugging Face, and Pollinations fallback
  web_search.py                  Live query and weather helpers
  auth/                          Local SQLite authentication and profiles
  database/                      SQLite schema and persistence helpers
  multimodal/                    Image OCR history and persistence
  multilingual/                  Detection, translation, language policy, voice config
  research/                      arXiv/local paper search, citations, timeline data
  sentiment/                     Sentiment detection, badges, analytics persistence
  vector_store/                  FAISS indexes and uploaded documents
  medquad_data/                  MedQuAD dataset files
  generated_images/              Generated image outputs
```

## Installation

```bash
cd streamlit-chatbot
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

On Linux/macOS, activate with:

```bash
source .venv/bin/activate
```

## Environment Variables

| Variable | Required | Description |
|---|---:|---|
| `GEMINI_API_KEY` | Yes for Gemini | Google Gemini API key. Can also be entered in the app Settings sidebar. |
| `HF_TOKEN` or `HUGGINGFACE_API_KEY` | Optional | Enables Hugging Face image-generation fallback. |
| `OMNICHAT_DB_PATH` | Optional | Custom SQLite database path. Defaults to `database/omnichat.db`. |

Never hardcode API keys in source files.

## Run

```bash
cd streamlit-chatbot
streamlit run app.py
```

Default local URL:

```text
http://localhost:8501
```

## Pages And Modes

- `Dashboard`: operational metrics for chats, knowledge base, image history, medical DB status, and sentiment mix.
- `General Assistant`: everyday Gemini assistant with live search and image generation intent detection.
- `Knowledge Base Assistant`: answers from uploaded documents first, then clearly labels any general-knowledge fallback.
- `Knowledge Management`: full document upload, deletion, watched-folder sync, refresh, and rebuild controls.
- `Medical Assistant`: MedQuAD-backed medical search with entities, confidence, citations, and disclaimer.
- `Research Assistant`: CS paper search, summarization, follow-up support, citations, related papers, and timeline.
- `Image Analysis`: multiple image upload, OCR, preview, history, and Gemini Vision Q&A.
- `Sentiment Analytics`: persisted sentiment history, labels, confidence, and charts.
- `Settings`: profile, language, theme, API, and voice-ready architecture configuration.

## Screenshots Placeholders

```text
docs/screenshots/dashboard.png
docs/screenshots/knowledge-management.png
docs/screenshots/research-assistant.png
docs/screenshots/image-analysis.png
docs/screenshots/sentiment-analytics.png
```

## Production Notes

- The local SQLite authentication layer is suitable for demos and internal prototypes. Use a managed identity provider for public production deployments.
- OCR requires Tesseract. Scanned PDF OCR also requires Poppler.
- The sentiment service uses a locally cached Transformers model when available and a deterministic lexical fallback otherwise.
- arXiv search uses the public arXiv API when the network is available and falls back to a local CS corpus.
- FAISS indexes are stored locally; back them up or mount persistent storage in deployment.

## Verification

Use these checks before deployment:

```bash
python -m compileall .
streamlit run app.py
```

