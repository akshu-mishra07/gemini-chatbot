"""
medical_retriever.py - Retrieval engine for the MedQuAD medical vector store.

Queries the medical FAISS database and returns structured context results.
"""

import os
import streamlit as st
from medical_vector_store import load_medical_vector_store, get_medical_index_path

@st.cache_data(show_spinner=False)
def _cached_query_medical_db(question: str, entities_tuple: tuple[str, ...], k: int, index_mtime: float) -> list[dict]:
    db = load_medical_vector_store()
    if db is None:
        print("Medical database is not initialized or loaded.")
        return []

    try:
        # 1. Retrieve a larger candidate pool first (e.g. 10 candidates)
        k_initial = max(k * 2, 10)
        docs_and_scores = db.similarity_search_with_score(question, k=k_initial)
        
        # 2. Tokenize question to extract keywords
        import re
        words = set(re.findall(r'\b\w+\b', question.lower()))
        stop_words = {
            "what", "how", "why", "who", "causes", "treatment", "symptoms", "signs", 
            "is", "are", "of", "the", "a", "an", "for", "with", "in", "on", "about", 
            "do", "does", "did", "to", "and", "or", "but", "if", "then", "else", "caused"
        }
        query_keywords = words - stop_words
        
        reranked_results = []
        for doc, score in docs_and_scores:
            # L2 distance is mapped to base similarity [0.0, 1.0]
            base_sim = max(0.0, min(1.0, 1.0 - (float(score) / 2.0)))
            
            focus = doc.metadata.get("focus", "").lower()
            synonyms = doc.metadata.get("synonyms", "").lower()
            
            focus_words = set(re.findall(r'\b\w+\b', focus))
            syn_words = set(re.findall(r'\b\w+\b', synonyms))
            
            # Check for keyword overlap or substring matches
            has_focus_match = bool(query_keywords.intersection(focus_words)) or (any(kw in focus for kw in query_keywords if len(kw) > 3))
            has_syn_match = bool(query_keywords.intersection(syn_words)) or (any(kw in synonyms for kw in query_keywords if len(kw) > 3))
            
            # Entity matching: Check if any detected medical entities match focus or synonyms
            has_entity_match = False
            if entities_tuple:
                entity_set = {ent.lower() for ent in entities_tuple}
                if any(ent in focus or ent in synonyms for ent in entity_set):
                    has_entity_match = True
            
            boost = 0.0
            if has_entity_match:
                boost += 0.45  # Strong boost for explicit medical entities matching
            elif has_focus_match:
                boost += 0.25
            elif has_syn_match:
                boost += 0.10
                
            boosted_sim = min(1.0, base_sim + boost)
            
            reranked_results.append({
                "content": doc.page_content,
                "source": doc.metadata.get("source", "Unknown"),
                "question": doc.metadata.get("question", ""),
                "answer": doc.metadata.get("answer", ""),
                "focus": doc.metadata.get("focus", ""),
                "qtype": doc.metadata.get("qtype", ""),
                "synonyms": doc.metadata.get("synonyms", ""),
                "score": float(score),
                "similarity": boosted_sim
            })
            
        # 3. Sort by boosted similarity in descending order
        reranked_results.sort(key=lambda x: x["similarity"], reverse=True)
        
        # 4. Return top k results
        return reranked_results[:k]
        
    except Exception as e:
        print(f"Error querying medical vector store: {e}")
        return []

import concurrent.futures
import sys

def _is_greeting(text: str) -> bool:
    cleaned = text.strip().lower().rstrip("?.!")
    greetings = {"hi", "hello", "hey", "good morning", "good evening", "good afternoon", "greetings"}
    return cleaned in greetings

MEDICAL_RETRIEVAL_TIMEOUT_SECONDS = 60.0
_medical_retrieval_executor = concurrent.futures.ThreadPoolExecutor(max_workers=2, thread_name_prefix="Med_Retrieval")

def query_medical_db(question: str, entities: tuple[str, ...] = (), k: int = 5) -> list[dict]:
    """
    Queries the dedicated medical vector store for the top k most relevant medical Q&A pairs.
    Includes a greeting check, medical entity boosting, and a bounded execution timeout.
    """
    if _is_greeting(question):
        print(f"[Stage 2: Retrieval Skipped] Greeting detected: {repr(question)}", file=sys.stderr)
        return []

    index_path = get_medical_index_path()
    file_path = os.path.join(index_path, "index.faiss")
    mtime = os.path.getmtime(file_path) if os.path.exists(file_path) else 0.0

    print(f"[Stage 2: Retrieval Started] medical search for: {repr(question)} with entities: {entities}", file=sys.stderr)
    
    future = _medical_retrieval_executor.submit(_cached_query_medical_db, question, entities, k, mtime)
    try:
        results = future.result(timeout=MEDICAL_RETRIEVAL_TIMEOUT_SECONDS)
        print(f"[Stage 2: Retrieval Completed] Found {len(results)} matches.", file=sys.stderr)
        return results
    except concurrent.futures.TimeoutError:
        print(f"[Stage 2: Retrieval WARNING] Medical search timed out after {MEDICAL_RETRIEVAL_TIMEOUT_SECONDS:.0f} seconds. Continuing without context.", file=sys.stderr)
        return []
    except Exception as e:
        print(f"[Stage 2: Retrieval ERROR] Medical search failed: {e}. Continuing without context.", file=sys.stderr)
        return []

def format_medical_context(chunks: list[dict]) -> str:
    """
    Formats retrieved medical Q&A chunks into a single text context block for Gemini.
    """
    if not chunks:
        return "No direct MedQuAD matching records found."

    formatted_parts = []
    for idx, chunk in enumerate(chunks):
        formatted_parts.append(
            f"--- Medical Source Record [{idx + 1}] (Focus: {chunk['focus']}, Source: {chunk['source']}) ---\n"
            f"Question: {chunk['question']}\n"
            f"Known Medical Answer: {chunk['answer']}"
        )
    return "\n\n".join(formatted_parts)
