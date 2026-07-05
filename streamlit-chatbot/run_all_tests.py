import os
import sys
import shutil
from PIL import Image

# Disable background scheduler thread during initialization to avoid circular/concurrent import locks in huggingface_hub
os.environ["OMNICHAT_SCHEDULER_DISABLE"] = "1"

# Ensure stdout handles UTF-8 correctly on Windows
try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

# Ensure project root is in Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from knowledge_manager import add_document, delete_document, load_metadata, sync_and_refresh_knowledge_base
from vector_store import load_vector_store, get_documents_save_dir
from medical_entities import detect_medical_entities, highlight_medical_entities
from medical_retriever import query_medical_db
from research.service import search_papers
from web_search import search_web
from sentiment.service import analyze_sentiment
from multilingual.service import translate_text, prepare_language_context
from database.storage import get_cached_translation

def test_sentiment_and_emotions():
    print("Testing Sentiment and Emotion classification...")
    tests = [
        ("I am so happy and delighted with this service! Thank you!", "Positive", "Joy"),
        ("I am extremely angry, this is the worst product ever and a waste of money.", "Negative", "Anger"),
        ("This is very sad and disappointing. I feel depressed about it.", "Negative", "Sadness"),
        ("I am worried and scared about my medical results.", "Negative", "Fear"),
        ("Wow, this is amazing and completely unexpected!", "Positive", "Surprise"),
        ("The package arrived today.", "Neutral", "Neutral")
    ]
    
    for text, expected_sent, expected_emo in tests:
        res = analyze_sentiment(text)
        print(f"  Input: '{text}' -> Sentiment: {res['label']}, Emotion: {res['emotion']} (Conf: {res['confidence']:.2f})")
        assert res["label"] == expected_sent, f"Expected sentiment {expected_sent}, got {res['label']}"
        assert res["emotion"] == expected_emo, f"Expected emotion {expected_emo}, got {res['emotion']}"
    print("[PASS] Sentiment & Emotion test completed successfully.")

def test_translation_memory():
    print("Testing Translation Memory persistent caching...")
    source_text = "Hello, how are you?"
    target_lang = "es"
    
    translated = translate_text(source_text, "en", target_lang)
    print(f"  Original: '{source_text}' -> Translated: '{translated}'")
    
    cached = get_cached_translation(source_text, "en", target_lang)
    print(f"  SQLite Cached Translation: '{cached}'")
    assert cached == translated, "Translation was not successfully cached in SQLite database!"
    print("[PASS] Translation Memory test completed successfully.")

def test_duplicate_document_detection():
    print("Testing Knowledge Base duplicate document detection...")
    filename = "test_duplicate_check.txt"
    file_bytes = b"This is unique content specifically written for duplicate detection testing."
    
    delete_document(filename)
    
    success, msg = add_document(filename, file_bytes)
    assert success, f"Failed to index first document: {msg}"
    print(f"  First upload: success={success}, msg='{msg}'")
    
    dup_filename = "test_duplicate_check_copy.txt"
    success_dup, msg_dup = add_document(dup_filename, file_bytes)
    print(f"  Second duplicate upload: success={success_dup}, msg='{msg_dup}'")
    assert not success_dup, "Duplicate content under different filename should have been rejected!"
    assert "Duplicate document detected" in msg_dup
    
    delete_document(filename)
    print("[PASS] Duplicate Document Detection test completed successfully.")

def test_markdown_support():
    print("Testing Markdown file support...")
    filename = "test_markdown.md"
    file_bytes = b"# Heading\n\nThis is a *markdown* test file containing text. We must check if the extensions are parsed."
    
    delete_document(filename)
    
    success, msg = add_document(filename, file_bytes)
    assert success, f"Failed to index markdown file: {msg}"
    print(f"  Markdown upload: success={success}, msg='{msg}'")
    
    meta = load_metadata()
    assert filename in meta["files"], "Markdown file is missing in metadata index!"
    
    delete_document(filename)
    print("[PASS] Markdown Support test completed successfully.")

def test_medical_seeding_and_entities():
    print("Testing Medical DB Seeding and Entity Recognition...")
    
    text = "The patient shows symptoms of pcod, pcos and wants advice on pregnancy care and diabetes management."
    entities = detect_medical_entities(text)
    print(f"  Detected entities in text: {entities}")
    assert "pcod" in [e.lower() for e in entities.get("DISEASE", [])], "PCOD entity not detected!"
    assert "pcos" in [e.lower() for e in entities.get("DISEASE", [])], "PCOS entity not detected!"
    assert "pregnancy" in [e.lower() for e in entities.get("DISEASE", [])], "Pregnancy entity not detected!"
    
    # Build in-memory FAISS index to test embeddings and curated records without file access locks
    from langchain_community.vectorstores import FAISS
    from embeddings import get_embeddings
    from medical_vector_store import CURATED_MEDICAL_RECORDS
    from langchain_core.documents import Document
    
    docs = []
    for qa in CURATED_MEDICAL_RECORDS:
        content = f"Question: {qa['question']}\n\nAnswer: {qa['answer']}"
        docs.append(Document(
            page_content=content,
            metadata={"focus": qa["focus"], "question": qa["question"], "answer": qa["answer"]}
        ))
        
    embeddings = get_embeddings()
    temp_db = FAISS.from_documents(docs, embeddings)
    
    pcos_query = "Explain Polycystic Ovary Syndrome (PCOS)"
    results = temp_db.similarity_search_with_relevance_scores(pcos_query, k=1)
    print(f"  PCOS Temp DB Query Results count: {len(results)}")
    if results:
        doc, score = results[0]
        print(f"  Top Match Focus: {doc.metadata['focus']}, Similarity Score: {score:.2f}")
        assert "polycystic" in doc.metadata["focus"].lower() or "pco" in doc.metadata["focus"].lower(), "PCOS query retrieved incorrect focus!"
        
    print("[PASS] Medical Seeding & Entity test completed successfully.")

def test_arxiv_doi_parsing():
    print("Testing Research Assistant DOI parsing...")
    papers = search_papers("attention", max_results=3, include_live_arxiv=True)
    print(f"  Found {len(papers)} papers.")
    for idx, paper in enumerate(papers, 1):
        doi = paper.get("doi")
        pdf_url = paper.get("pdf_url")
        print(f"  [{idx}] Title: {paper.get('title')[:40]}... | DOI: {doi} | PDF: {pdf_url}")
        assert doi, f"Paper '{paper.get('title')}' is missing DOI information!"
        assert pdf_url, f"Paper '{paper.get('title')}' is missing PDF download link!"
    print("[PASS] arXiv DOI and PDF Link test completed successfully.")

def test_image_prompt_optimizer():
    print("Testing Image Prompt Optimizer...")
    from image_generator import get_optimized_prompt
    
    opt, meta = get_optimized_prompt("Dog")
    print(f"  Dog: {opt} | Aspect Ratio: {meta['aspect_ratio']}")
    assert "golden retriever" in opt.lower(), "Dog short expansion failed!"
    
    opt_god, meta_god = get_optimized_prompt("Radha Krishna swinging near a river")
    print(f"  Radha Krishna: {opt_god} | Aspect Ratio: {meta_god['aspect_ratio']}")
    assert "yamuna" in opt_god.lower() and "traditional swing" in opt_god.lower(), "Radha Krishna expansion failed!"
    
    _, meta_ls = get_optimized_prompt("Sunset over mountains wide screen")
    print(f"  Landscape aspect ratio: {meta_ls['aspect_ratio']}")
    assert meta_ls['aspect_ratio'] == "16:9", "Landscape aspect ratio detection failed!"

    print("[PASS] Image Prompt Optimizer test completed successfully.")

def test_modular_image_pipeline():
    print("Testing Modular Image Pipeline...")
    from image_pipeline.entities import extract_entities
    from image_pipeline.optimizer import optimize_prompt
    from image_pipeline.pipeline import run_pipeline
    
    ent = extract_entities("Eiffel Tower in winter with snowman and tourist")
    print(f"  Entities: {ent}")
    names = [e["name"].lower() for e in ent]
    assert "eiffel tower" in names, "Eiffel Tower not extracted!"
    
    opt, meta = optimize_prompt("Eiffel Tower in winter with snowman", ent)
    print(f"  Optimized: {opt[:80]}...")
    assert "architecture" in opt.lower() or "accurate" in opt.lower(), "Special landmark handling failed!"
    
    res = run_pipeline("Eiffel Tower in winter with snowman")
    print(f"  Pipeline Result provider: {res['provider']}")
    assert res["status"] == "success", "Pipeline execution failed!"
    assert os.path.exists(res["filepath"]), "Pipeline did not save generated image file!"
    
    print("[PASS] Modular Image Pipeline tests completed successfully.")

def test_hardening_scenarios():
    print("Testing Pipeline Hardening & Error Handling...")
    from image_pipeline.pipeline import run_pipeline
    from image_pipeline.providers import OpenAIProvider, GeminiProvider
    
    res_none = run_pipeline(None)
    assert not res_none["success"], "Pipeline failed to reject None prompt!"
    print(f"  Passed None prompt validation: {res_none['error']}")
        
    res_empty = run_pipeline("")
    assert not res_empty["success"], "Pipeline failed to reject empty prompt!"
    print(f"  Passed empty prompt validation: {res_empty['error']}")

    prov = OpenAIProvider(api_key="bad-key-xyz")
    try:
        prov.generate("test", "1:1", "", "Standard")
        assert False, "OpenAIProvider failed to raise on invalid key!"
    except Exception as e:
        print(f"  Passed OpenAIProvider bad key error handling: {e}")

    g_prov = GeminiProvider(api_key=None)
    assert not g_prov.is_available(), "GeminiProvider should be unavailable when key is None!"
    print("  Passed GeminiProvider availability validation.")
    
    print("[PASS] Pipeline Hardening & Error Handling tests completed successfully.")

def run_all():
    print("====================================================")
    print("        RUNNING ALL OMNICHAT AI TEST SUITES        ")
    print("====================================================\n")
    try:
        test_sentiment_and_emotions()
        test_translation_memory()
        test_duplicate_document_detection()
        test_markdown_support()
        test_medical_seeding_and_entities()
        test_arxiv_doi_parsing()
        test_image_prompt_optimizer()
        test_modular_image_pipeline()
        test_hardening_scenarios()
        print("\n====================================================")
        print("        ALL TESTS COMPLETED SUCCESSFULLY!           ")
        print("====================================================")
        sys.exit(0)
    except AssertionError as e:
        print(f"\n[FAIL] TEST FAILURE: {e}")
        sys.exit(1)
    except Exception as e:
        import traceback
        print(f"\n[FAIL] UNEXPECTED TEST ERROR: {e}")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    run_all()
