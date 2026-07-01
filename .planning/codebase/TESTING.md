# Testing Patterns

**Analysis Date:** 2026-07-01

## Test Framework

**Runner:**
- No official runner (e.g., pytest, unittest) is currently integrated into the main `requirements.txt` dependencies.

**Verification Commands:**
```bash
python -m compileall .                      # Verify file syntax and compile all python modules
streamlit run app.py                        # Manual verification of layouts and features
```

## Test File Organization

**Ad-hoc Scripts:**
- Individual testing scripts are placed in the app directory root rather than a dedicated `tests/` directory:
  - `verify_image_gen.py` - Runs text-to-image pipeline tests for Imagen, HF, and Pollinations.
  - `run_reconstruct_v4_test.py` - Runs disassembly recovery logic tests.
  - `check_syntax.py` - Script verifying codebase syntax.
  - `check_messages.py` - Script verifying message schemas.

## Mocking & Fallback Testing

**In-Code Fallbacks:**
- Instead of mocks, testing API boundaries is done by observing fallback code paths.
- Local dictionaries (e.g., `LOCAL_GREETINGS` and `LOCAL_KNOWLEDGE_BASE` in `app.py`) are used to verify how the application acts when the Google Gemini service throws quota or authentication errors.
- A local CS papers list in `research/service.py` is used to test the CS research page when arXiv is unavailable.

## Coverage

**Target:**
- No automated coverage tracking is configured. 
- Validation relies on syntax checks and manual feature runs.

---

*Testing analysis: 2026-07-01*
*Update when introducing testing frameworks (e.g. pytest)*
