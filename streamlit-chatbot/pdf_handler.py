"""
pdf_handler.py - PDF ingestion and semantic search via TF-IDF + FAISS.

Why TF-IDF instead of Gemini embedding API:
  The google-genai SDK defaults to the v1beta endpoint, but text-embedding-004
  only exists on the v1 endpoint — causing a 404 NOT_FOUND at runtime.
  TF-IDF + FAISS is offline, API-version-agnostic, and works reliably in all
  environments without an internet connection.

Pipeline:
  1.  Extract text from PDF using pypdf.
  2.  Split into overlapping chunks via LangChain's RecursiveCharacterTextSplitter.
  3.  Fit a TF-IDF vectorizer on all chunks.
  4.  Project sparse TF-IDF vectors to 256-dim dense space with TruncatedSVD (LSA).
  5.  L2-normalise the dense vectors.
  6.  Index them in a FAISS IndexFlatIP (inner-product = cosine on unit vectors).
  7.  At query time: vectorise → project → normalise → FAISS search → return chunks.
"""

import io
import re
import numpy as np
import faiss
from pypdf import PdfReader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import TruncatedSVD

# Dimensionality of the dense projection.
# 256 is a good balance: rich enough for quality search, small enough to be fast.
_SVD_COMPONENTS = 256

# Chunking parameters (character-level)
_CHUNK_SIZE = 800       # max characters per chunk
_CHUNK_OVERLAP = 120    # character overlap between consecutive chunks


# ---------------------------------------------------------------------------
# Text extraction
# ---------------------------------------------------------------------------

def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    """
    Extract all text from a PDF file.

    Args:
        pdf_bytes: Raw bytes of the uploaded PDF.

    Returns:
        str: Concatenated text from all pages.

    Raises:
        ValueError: If no readable text is found.
    """
    reader = PdfReader(io.BytesIO(pdf_bytes))
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text and text.strip():
            pages.append(text.strip())

    if not pages:
        raise ValueError(
            "No extractable text found. "
            "The PDF may be image-based or password-protected."
        )

    return "\n\n".join(pages)


# ---------------------------------------------------------------------------
# Text chunking
# ---------------------------------------------------------------------------

def chunk_text(text: str) -> list[str]:
    """
    Split text into overlapping chunks using a recursive separator strategy:
    paragraph → sentence → word boundaries, in that order.

    Args:
        text: Full extracted document text.

    Returns:
        list[str]: Non-empty chunks, each at most _CHUNK_SIZE characters.

    Raises:
        ValueError: If no chunks can be produced.
    """
    def _split(text: str, separators: list[str]) -> list[str]:
        """Recursively split on the first effective separator."""
        if not separators or len(text) <= _CHUNK_SIZE:
            return [text] if text.strip() else []

        sep = separators[0]
        rest = separators[1:]

        parts = re.split(re.escape(sep), text) if sep else list(text)

        # If this separator gave only one piece, try the next one
        if len(parts) <= 1:
            return _split(text, rest)

        chunks: list[str] = []
        current = ""
        for part in parts:
            candidate = (current + sep + part).strip() if current else part.strip()
            if len(candidate) <= _CHUNK_SIZE:
                current = candidate
            else:
                if current:
                    chunks.append(current)
                # Part itself may be too long — recurse on it
                if len(part) > _CHUNK_SIZE:
                    chunks.extend(_split(part.strip(), rest))
                    current = ""
                else:
                    current = part.strip()
        if current:
            chunks.append(current)
        return chunks

    raw = _split(text, ["\n\n", "\n", ". ", " "])

    # Apply overlap: prepend the tail of the previous chunk to the next one
    overlapped: list[str] = []
    for i, chunk in enumerate(raw):
        if i == 0 or _CHUNK_OVERLAP == 0:
            overlapped.append(chunk)
        else:
            tail = overlapped[-1][-_CHUNK_OVERLAP:].strip()
            merged = (tail + " " + chunk).strip()
            overlapped.append(merged[:_CHUNK_SIZE])

    result = [c for c in overlapped if c.strip()]
    if not result:
        raise ValueError("Document text could not be split into chunks.")
    return result


# ---------------------------------------------------------------------------
# Embedding via TF-IDF + Latent Semantic Analysis (TruncatedSVD)
# ---------------------------------------------------------------------------

def _fit_vectorizer(chunks: list[str]) -> tuple:
    """
    Fit TF-IDF + SVD on the provided chunks and return the fitted objects
    along with the normalised dense matrix.

    Args:
        chunks: List of text chunks.

    Returns:
        tuple: (TfidfVectorizer, TruncatedSVD, np.ndarray dense_matrix)
               dense_matrix shape: (n_chunks, _SVD_COMPONENTS), L2-normalised.
    """
    # Use sublinear TF scaling for better weighting of common terms
    vectorizer = TfidfVectorizer(
        sublinear_tf=True,
        min_df=1,
        max_features=20_000,
        ngram_range=(1, 2),
    )
    tfidf_matrix = vectorizer.fit_transform(chunks)   # sparse (n, vocab)

    # Project to dense space via Latent Semantic Analysis
    n_components = min(_SVD_COMPONENTS, tfidf_matrix.shape[1] - 1, len(chunks) - 1)
    n_components = max(n_components, 1)

    svd = TruncatedSVD(n_components=n_components, random_state=42)
    dense = svd.fit_transform(tfidf_matrix).astype(np.float32)  # (n, dim)

    # L2-normalise so inner-product == cosine similarity
    norms = np.linalg.norm(dense, axis=1, keepdims=True) + 1e-10
    dense /= norms

    return vectorizer, svd, dense


def build_faiss_index(dense: np.ndarray) -> faiss.Index:
    """
    Build and populate a FAISS IndexFlatIP from a dense normalised matrix.

    Args:
        dense: L2-normalised matrix of shape (n_chunks, dim).

    Returns:
        faiss.Index: Populated FAISS index ready for search.
    """
    dim = dense.shape[1]
    index = faiss.IndexFlatIP(dim)   # cosine on unit vectors
    index.add(dense)
    return index


# ---------------------------------------------------------------------------
# Query-time retrieval
# ---------------------------------------------------------------------------

def _embed_query(
    query: str,
    vectorizer: TfidfVectorizer,
    svd: TruncatedSVD,
) -> np.ndarray:
    """
    Transform a query string into the same dense vector space as the corpus.

    Args:
        query: User question (English).
        vectorizer: Fitted TfidfVectorizer.
        svd: Fitted TruncatedSVD.

    Returns:
        np.ndarray: L2-normalised dense query vector of shape (1, dim).
    """
    sparse = vectorizer.transform([query])
    dense = svd.transform(sparse).astype(np.float32)
    norm = np.linalg.norm(dense) + 1e-10
    return dense / norm


def search_context(
    query: str,
    index: faiss.Index,
    chunks: list[str],
    vectorizer: TfidfVectorizer,
    svd: TruncatedSVD,
    k: int = 4,
) -> str:
    """
    Retrieve the k most relevant chunks for a query using FAISS cosine search.

    Args:
        query: User question in English.
        index: FAISS IndexFlatIP built from chunk embeddings.
        chunks: Original text chunks (parallel to the index).
        vectorizer: Fitted TfidfVectorizer.
        svd: Fitted TruncatedSVD.
        k: Number of top chunks to retrieve.

    Returns:
        str: Relevant passages joined by dividers.
    """
    query_vec = _embed_query(query, vectorizer, svd)
    k = min(k, len(chunks))
    scores, indices = index.search(query_vec, k)

    relevant = [
        chunks[idx]
        for idx in indices[0]
        if 0 <= idx < len(chunks)
    ]
    return "\n\n— — —\n\n".join(relevant)


# ---------------------------------------------------------------------------
# Full pipeline entry point
# ---------------------------------------------------------------------------

def process_pdf(pdf_bytes: bytes) -> tuple:
    """
    Run the full ingestion pipeline on a PDF file.

    Steps: extract → chunk → TF-IDF fit → SVD project → L2 normalise → FAISS index.

    Args:
        pdf_bytes: Raw bytes of the uploaded PDF.

    Returns:
        tuple: (faiss.Index, list[str] chunks, TfidfVectorizer, TruncatedSVD, str full_text)

    Raises:
        ValueError: If the PDF has no extractable text.
    """
    full_text = extract_text_from_pdf(pdf_bytes)
    chunks = chunk_text(full_text)

    vectorizer, svd, dense = _fit_vectorizer(chunks)
    index = build_faiss_index(dense)

    return index, chunks, vectorizer, svd, full_text
