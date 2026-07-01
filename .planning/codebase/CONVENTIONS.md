# Coding Conventions

**Analysis Date:** 2026-07-01

## Naming Patterns

**Files:**
- Snake case for all Python files (e.g., `document_processor.py`, `knowledge_manager.py`, `medical_retriever.py`).
- Lowercase directories matching service names (e.g., `auth`, `database`, `multilingual`, `multimodal`, `research`, `sentiment`).

**Functions:**
- Snake case for all functions (e.g., `init_session_state`, `send_message_stream`, `load_session`, `is_datetime_query`).
- Descriptors prefixing intent: `is_*` for booleans, `get_*` for fetchers, `render_*` for Streamlit view layout elements.

**Variables:**
- Snake case for variables (e.g., `weather_location`, `full_text`, `uploaded_files`).
- Upper snake case for global constants (e.g., `PREMIUM_CSS`, `LOCAL_KNOWLEDGE_BASE`, `ASSISTANT_MODES`).

## Code Style

**Formatting:**
- standard PEP 8 rules.
- 4-space indentation.
- Double quotes for docstrings and standard strings; single quotes optionally inside dictionaries or simple lookups.
- Section headers separated by comment dashes:
  ```python
  # ---------------------------------------------------------------------------
  # Section Name
  # ---------------------------------------------------------------------------
  ```

**Linting:**
- Checked via syntax compiles: `python -m compileall .` prior to run validations.
- No print statement blocking: logs to stderr are preferred for daemon troubleshooting.

## Import Organization

**Order:**
1. Standard libraries (e.g., `import os`, `import sys`, `import datetime`).
2. Streamlit import: `import streamlit as st`.
3. Major third-party dependencies (e.g., `import faiss`, `import numpy`, `import pandas`).
4. Project modules imported as explicit name groups:
   ```python
   from chatbot import send_message_stream
   from auth.service import authenticate_user
   ```

## Error Handling

**Patterns:**
- Try/except blocks are required for all external API connections (Gemini, arXiv, weather scraping).
- Custom fallback actions must be specified inside catch blocks to prevent system crashes (e.g., fallback local greeting, fallback search query).
- Stream loops catch exceptions and render them inline with warning blocks.

**Logging:**
- Service boundary failures must print detailed logs to stderr: `print(f"[Error Type] {exc}", file=sys.stderr)`.

## Comments

**Docstrings:**
- Module docstrings at the beginning of files explaining the component's goal.
- Docstrings for functions specifying input and return characteristics.

**TODO Formatting:**
- Inline comments: `# TODO: description` or `# Note: context`.

## Function Design

**Structure:**
- Keep functions single-purpose (e.g., separating database writes, prompt parsing, and UI rendering).
- Early returns to handle input validation / guard clauses.
- Explicit returns; no implicit `None` values unless expected.

---

*Convention analysis: 2026-07-01*
*Update when coding conventions evolve*
