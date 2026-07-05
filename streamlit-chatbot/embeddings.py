"""
embeddings.py - Embedding model module with SQLite-backed caching.

Provides a cached, singleton instance of HuggingFaceEmbeddings wrapped in a SQLite cache
to prevent redundant embedding generation and optimize performance.
"""

import os
import json
import hashlib
import sqlite3
import streamlit as st

try:
    from langchain_core.embeddings import Embeddings
except ImportError:
    try:
        from langchain_community.embeddings import Embeddings
    except ImportError:
        Embeddings = object

class CachedEmbeddings(Embeddings):
    """
    Wrapper around LangChain Embeddings that caches generated vectors in a SQLite database
    to avoid slow, repetitive calculations on CPU.
    """
    def __init__(self, base_embeddings, cache_dir="./vector_store"):
        self.base_embeddings = base_embeddings
        self.db_path = os.path.normpath(os.path.join(cache_dir, "embedding_cache.db"))
        os.makedirs(cache_dir, exist_ok=True)
        self._init_db()

    def __call__(self, text):
        if isinstance(text, list):
            return self.embed_documents(text)
        return self.embed_query(text)

    def _init_db(self):
        conn = sqlite3.connect(self.db_path, timeout=10)
        conn.execute(
            "CREATE TABLE IF NOT EXISTS cache (text_hash TEXT PRIMARY KEY, embedding TEXT)"
        )
        conn.commit()
        conn.close()

    def _get_hash(self, text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        
        results = [None] * len(texts)
        missing_indices = []
        missing_texts = []
        
        conn = sqlite3.connect(self.db_path, timeout=10)
        cursor = conn.cursor()
        
        for idx, text in enumerate(texts):
            thash = self._get_hash(text)
            cursor.execute("SELECT embedding FROM cache WHERE text_hash = ?", (thash,))
            row = cursor.fetchone()
            if row:
                results[idx] = json.loads(row[0])
            else:
                missing_indices.append(idx)
                missing_texts.append(text)
                
        if missing_texts:
            computed = self.base_embeddings.embed_documents(missing_texts)
            for idx, text, emb in zip(missing_indices, missing_texts, computed):
                results[idx] = emb
                thash = self._get_hash(text)
                cursor.execute(
                    "INSERT OR REPLACE INTO cache (text_hash, embedding) VALUES (?, ?)",
                    (thash, json.dumps(emb))
                )
            conn.commit()
            
        conn.close()
        return results

    def embed_query(self, text: str) -> list[float]:
        if not text:
            return []
            
        thash = self._get_hash(text)
        conn = sqlite3.connect(self.db_path, timeout=10)
        cursor = conn.cursor()
        cursor.execute("SELECT embedding FROM cache WHERE text_hash = ?", (thash,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return json.loads(row[0])
            
        emb = self.base_embeddings.embed_query(text)
        conn = sqlite3.connect(self.db_path, timeout=10)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT OR REPLACE INTO cache (text_hash, embedding) VALUES (?, ?)",
            (thash, json.dumps(emb))
        )
        conn.commit()
        conn.close()
        return emb


class FallbackEmbeddings(Embeddings):
    """
    A lightweight, pure-Python deterministic bag-of-words embedding model to use as fallback
    if HuggingFace/PyTorch DLL loading fails. Generates 384-dimensional unit vectors.
    """
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self.embed_query(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        import re
        import math
        
        words = re.findall(r"[a-z0-9]+", text.lower())
        vector = [0.0] * 384
        if not words:
            vector[0] = 1.0
            return vector
            
        stopwords = {
            "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are",
            "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by",
            "did", "do", "does", "doing", "down", "during", "each", "few", "for", "from", "further", "had",
            "has", "have", "having", "he", "her", "here", "hers", "him", "his", "how", "i", "if", "in", "into",
            "is", "it", "its", "me", "more", "most", "my", "myself", "no", "nor", "not", "of", "off", "on",
            "only", "or", "other", "our", "ours", "ourselves", "out", "over", "own", "same", "she", "should",
            "so", "some", "such", "than", "that", "the", "their", "theirs", "them", "themselves", "then",
            "there", "these", "they", "this", "those", "through", "to", "too", "under", "until", "up", "very",
            "was", "we", "were", "what", "when", "where", "which", "while", "who", "whom", "why", "with",
            "you", "your", "yours", "yourself", "yourselves"
        }
        
        def deterministic_hash(s: str) -> int:
            h = 2166136261
            for char in s:
                h = (h ^ ord(char)) * 16777619
                h &= 0xffffffff
            return h

        for word in words:
            if word in stopwords:
                continue
            idx = deterministic_hash(word) % 384
            vector[idx] += 1.0
            
        sq_sum = sum(x*x for x in vector)
        norm = math.sqrt(sq_sum) if sq_sum > 0 else 1.0
        return [x / norm for x in vector]

    def __call__(self, text):
        if isinstance(text, list):
            return self.embed_documents(text)
        return self.embed_query(text)


_cached_embeddings = None

@st.cache_resource(show_spinner=False)
def get_embeddings():
    """
    Get or initialize the CachedEmbeddings singleton instance.
    Uses 'sentence-transformers/all-MiniLM-L6-v2' on CPU, falling back to FallbackEmbeddings if needed.
    """
    global _cached_embeddings
    if _cached_embeddings is not None:
        return _cached_embeddings

    try:
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
        except ImportError:
            from langchain_community.embeddings import HuggingFaceEmbeddings
            
        base = HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={"device": "cpu"},
        )
        # Test if it actually works without DLL/import failures
        base.embed_query("test_probe")
    except Exception as e:
        import sys
        print(f"[Embeddings Load Warning] Failed to initialize base HuggingFaceEmbeddings ({e}). Using pure-Python deterministic fallback.", file=sys.stderr)
        base = FallbackEmbeddings()
        
    _cached_embeddings = CachedEmbeddings(base)
    return _cached_embeddings
