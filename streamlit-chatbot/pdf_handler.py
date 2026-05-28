"""
pdf_handler.py - PDF ingestion and semantic search module.

Pipeline:
  1. Extract text from PDF using pypdf.
  2. Split text into overlapping word-level chunks.
  3. Generate embeddings via the Gemini Embedding API (text-embedding-004).
     — No local model download, no torch/FAISS disk footprint.
  4. Retrieve top-k chunks at query time using numpy cosine similarity.

The retrieved chunks are injected into the Gemini prompt as grounding context.
"""

import io
import numpy as np
from pypdf import PdfReader
from google import genai

# Gemini embedding model
_EMBEDDING_MODEL = "text-embedding-004"

# Output dimensionality of text-embedding-004
_EMBED_DIM = 768


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """
    Compute cosine similarity between one query vector and a matrix of corpus vectors.

    Args:
        a: Query vector of shape (dim,).
        b: Corpus matrix of shape (n_chunks, dim).

    Returns:
        np.ndarray: Similarity scores of shape (n_chunks,).
    """
    a_norm = a / (np.linalg.norm(a) + 1e-10)
    b_norms = b / (np.linalg.norm(b, axis=1, keepdims=True) + 1e-10)
    return b_norms @ a_norm


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extract all text from a PDF file, joining pages with double newlines.

    Args:
        pdf_bytes: Raw bytes of the uploaded PDF.

    Returns:
        str: Combined text from all pages.

    Raises:
        ValueError: If no extractable text was found.
    """
    reader = PdfReader(io.BytesIO(pdf_bytes))
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text and text.strip():
            pages.append(text.strip())

    if not pages:
        raise ValueError(
            "No extractable text found in the PDF. "
            "The file may be image-based or password-protected."
        )

    return "\n\n".join(pages)


def chunk_text(
    text: str,
    chunk_size: int = 400,
    overlap: int = 60,
) -> list[str]:
    """
    Split text into overlapping word-level chunks.

    Args:
        text: Full extracted document text.
        chunk_size: Target number of words per chunk.
        overlap: Number of words shared between consecutive chunks.

    Returns:
        list[str]: Non-empty text chunks.
    """
    words = text.split()
    if not words:
        return []

    step = max(1, chunk_size - overlap)
    chunks = []
    for i in range(0, len(words), step):
        chunk = " ".join(words[i: i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)
    return chunks


def build_embeddings(
    client: genai.Client,
    chunks: list[str],
) -> np.ndarray:
    """
    Generate Gemini embeddings for all text chunks.

    Batches requests to avoid hitting per-request limits.
    Each chunk produces a 768-dimensional float vector.

    Args:
        client: Authenticated google.genai Client.
        chunks: List of text chunks.

    Returns:
        np.ndarray: Matrix of shape (n_chunks, 768).
    """
    vectors = []
    # Embed in small batches (API limit: ~100 texts per call)
    batch_size = 20
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i: i + batch_size]
        response = client.models.embed_content(
            model=_EMBEDDING_MODEL,
            contents=batch,
        )
        for emb in response.embeddings:
            vectors.append(emb.values)

    return np.array(vectors, dtype=np.float32)


def search_context(
    query: str,
    client: genai.Client,
    embeddings: np.ndarray,
    chunks: list[str],
    k: int = 4,
) -> str:
    """
    Retrieve the k most semantically relevant chunks for a query
    using cosine similarity between Gemini embeddings.

    Args:
        query: User's question (in English).
        client: Authenticated google.genai Client.
        embeddings: Pre-computed chunk embeddings of shape (n_chunks, dim).
        chunks: Original text chunks parallel to embeddings.
        k: Number of top results to return.

    Returns:
        str: Concatenated relevant passages separated by dividers.
    """
    # Embed the query
    query_response = client.models.embed_content(
        model=_EMBEDDING_MODEL,
        contents=[query],
    )
    query_vector = np.array(query_response.embeddings[0].values, dtype=np.float32)

    # Compute similarity scores and rank
    scores = _cosine_similarity(query_vector, embeddings)
    top_k_indices = np.argsort(scores)[::-1][:k]

    relevant = [chunks[idx] for idx in top_k_indices if 0 <= idx < len(chunks)]
    return "\n\n— — —\n\n".join(relevant)


def process_pdf(pdf_bytes: bytes, client: genai.Client) -> tuple:
    """
    Full ingestion pipeline: extract → chunk → embed.

    Args:
        pdf_bytes: Raw bytes of the uploaded PDF.
        client: Authenticated google.genai Client for embedding generation.

    Returns:
        tuple: (np.ndarray embeddings, list[str] chunks, str full_text)

    Raises:
        ValueError: If the PDF has no extractable text.
    """
    full_text = extract_text_from_pdf(pdf_bytes)

    chunks = chunk_text(full_text)
    if not chunks:
        raise ValueError("PDF text could not be split into chunks.")

    embeddings = build_embeddings(client, chunks)
    return embeddings, chunks, full_text
