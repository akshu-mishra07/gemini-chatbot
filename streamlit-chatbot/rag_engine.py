"""
rag_engine.py - RAG query and context formatting module.

Performs semantic search on the FAISS store and prepares prompts with citations.
"""

import os
import re
import streamlit as st
from vector_store import load_vector_store, get_index_path


import concurrent.futures
import sys

def _is_greeting(text: str) -> bool:
    cleaned = text.strip().lower().rstrip("?.!")
    greetings = {"hi", "hello", "hey", "good morning", "good evening", "good afternoon", "greetings"}
    return cleaned in greetings

@st.cache_data(show_spinner=False)
def _cached_query_relevant_chunks(question: str, k: int, index_mtime: float) -> list[dict]:
    db = load_vector_store()
    if db is None:
        return []

    try:
        # FAISS similarity_search_with_score returns list of tuples: (Document, score)
        # where score is L2 distance.
        docs_and_scores = db.similarity_search_with_score(question, k=k)
        
        results = []
        for doc, score in docs_and_scores:
            # Compress content: remove duplicate/extra whitespaces and newlines
            content = doc.page_content
            content = re.sub(r'[ \t]+', ' ', content)
            content = re.sub(r'\n+', '\n', content).strip()
            
            results.append({
                "content": content,
                "source": doc.metadata.get("source", "Unknown"),
                "chunk_index": doc.metadata.get("chunk_index", 0),
                "total_chunks": doc.metadata.get("total_chunks", 1),
                "score": float(score)
            })
        return results
    except Exception as e:
        print(f"Error querying FAISS: {e}", file=sys.stderr)
        return []


RETRIEVAL_TIMEOUT_SECONDS = 60.0
_retrieval_executor = concurrent.futures.ThreadPoolExecutor(max_workers=2, thread_name_prefix="RAG_Retrieval")

def query_relevant_chunks(question: str, k: int = 3) -> list[dict]:
    """
    Queries the FAISS vector database for the most relevant text chunks matching a question.
    Includes a greeting check and a bounded execution timeout.
    """
    if _is_greeting(question):
        print(f"[Stage 2: Retrieval Skipped] Greeting detected: {repr(question)}", file=sys.stderr)
        return []

    index_path = get_index_path()
    file_path = os.path.join(index_path, "index.faiss")
    mtime = os.path.getmtime(file_path) if os.path.exists(file_path) else 0.0

    print(f"[Stage 2: Retrieval Started] semantic search for: {repr(question)}", file=sys.stderr)
    
    future = _retrieval_executor.submit(_cached_query_relevant_chunks, question, k, mtime)
    try:
        results = future.result(timeout=RETRIEVAL_TIMEOUT_SECONDS)
        print(f"[Stage 2: Retrieval Completed] Found {len(results)} chunks.", file=sys.stderr)
        return results
    except concurrent.futures.TimeoutError:
        print(f"[Stage 2: Retrieval WARNING] Semantic search timed out after {RETRIEVAL_TIMEOUT_SECONDS:.0f} seconds. Continuing without context.", file=sys.stderr)
        return []
    except Exception as e:
        print(f"[Stage 2: Retrieval ERROR] Semantic search failed: {e}. Continuing without context.", file=sys.stderr)
        return []


def format_rag_context(chunks: list[dict]) -> str:
    """
    Formats the retrieved chunks into a unified context string for the LLM.
    """
    if not chunks:
        return "No relevant context found in uploaded documents."

    formatted_parts = []
    for idx, chunk in enumerate(chunks):
        formatted_parts.append(
            f"--- Context Segment [{idx + 1}] (Source: {chunk['source']}) ---\n"
            f"{chunk['content']}"
        )
    return "\n\n".join(formatted_parts)


def build_system_prompt_with_context(context_str: str) -> str:
    """
    Builds a system prompt instructing the model to prioritize document context.
    """
    return (
        "You are an expert AI assistant with access to a local knowledge base of uploaded documents. "
        "Your goal is to answer the user's question using the provided context as your primary source of truth.\n\n"
        "Instructions:\n"
        "1. Prioritize facts, numbers, and statements from the provided context.\n"
        "2. If the answer cannot be found in the context, you may use your general knowledge, "
        "but clearly state that the information was not found in the documents and that you are answering from general knowledge.\n"
        "3. Provide clean, professional answers. Refer to documents when citing facts.\n\n"
        f"--- DOCUMENTS CONTEXT ---\n{context_str}"
    )
