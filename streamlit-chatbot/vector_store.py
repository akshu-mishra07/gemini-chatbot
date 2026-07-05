from __future__ import annotations
"""
vector_store.py - FAISS database operations module.

Handles loading, saving, and updating the local FAISS index.
"""

import os
import shutil
import streamlit as st
from embeddings import get_embeddings

VECTOR_STORE_DIR = "./vector_store"
INDEX_NAME = "faiss_index"


def get_index_path() -> str:
    """
    Returns the folder path where the FAISS index is saved.
    """
    return os.path.join(VECTOR_STORE_DIR, INDEX_NAME)


def initialize_dirs():
    """
    Creates the vector store directory structure if it doesn't exist.
    """
    os.makedirs(VECTOR_STORE_DIR, exist_ok=True)
    os.makedirs(os.path.join(VECTOR_STORE_DIR, "documents"), exist_ok=True)
    os.makedirs(get_index_path(), exist_ok=True)


@st.cache_resource(show_spinner=False)
def _cached_load_vector_store(index_path: str, index_mtime: float):
    from langchain_community.vectorstores import FAISS
    embeddings = get_embeddings()
    return FAISS.load_local(index_path, embeddings, allow_dangerous_deserialization=True)


def clear_vector_store_cache():
    """Clear only the cached KB FAISS loader instead of all Streamlit caches."""
    try:
        _cached_load_vector_store.clear()
    except Exception:
        pass
    try:
        import streamlit as st
        st.cache_data.clear()
    except Exception:
        pass


def load_vector_store() -> "FAISS" | None:
    """
    Loads the local FAISS index if it exists.

    Returns:
        FAISS | None: The loaded FAISS database, or None if it doesn't exist.
    """
    index_path = get_index_path()
    file_path = os.path.join(index_path, "index.faiss")
    if os.path.exists(file_path):
        try:
            mtime = os.path.getmtime(file_path)
            return _cached_load_vector_store(index_path, mtime)
        except Exception as e:
            print(f"Error loading FAISS store: {e}")
            return None
    return None


def save_vector_store(db: "FAISS"):
    """
    Saves the FAISS index locally.
    """
    initialize_dirs()
    index_path = get_index_path()
    db.save_local(index_path)
    clear_vector_store_cache()


def add_documents_to_store(documents: list) -> "FAISS":
    """
    Adds a list of LangChain Document chunks to the existing FAISS index, or creates a new one.

    Args:
        documents (list[Document]): List of Document objects to index.

    Returns:
        FAISS: The updated FAISS database instance.
    """
    from langchain_community.vectorstores import FAISS

    if not documents:
        db = load_vector_store()
        if db is None:
            raise ValueError("No documents provided to initialize a new vector store.")
        return db

    db = load_vector_store()
    embeddings = get_embeddings()
    if db is None:
        db = FAISS.from_documents(documents, embeddings)
    else:
        db.add_documents(documents)
    
    save_vector_store(db)
    return db


def rebuild_vector_store(all_documents: list) -> "FAISS" | None:
    """
    Deletes the existing FAISS index and builds a fresh one from the provided documents.

    Args:
        all_documents (list[Document]): Full list of all documents to be indexed.

    Returns:
        FAISS | None: The new FAISS database, or None if no documents were provided.
    """
    from langchain_community.vectorstores import FAISS

    index_path = get_index_path()
    
    # Remove existing index directories
    if os.path.exists(index_path):
        try:
            shutil.rmtree(index_path)
        except Exception as e:
            print(f"Warning: Could not remove old index directory: {e}")
    clear_vector_store_cache()

    if not all_documents:
        return None

    embeddings = get_embeddings()
    db = FAISS.from_documents(all_documents, embeddings)
    save_vector_store(db)
    return db


def get_documents_save_dir() -> str:
    """
    Returns the path where uploaded document files are persisted.
    """
    initialize_dirs()
    return os.path.join(VECTOR_STORE_DIR, "documents")
