"""
knowledge_manager.py - Knowledge Base Metadata, File Tracking, and Thread-Safe Sync module.

Tracks file stats, processes document persistence, manages deletions, and provides
an automatic sync/refresh check between the filesystem and the vector database
using a background scheduler thread.
"""

import os
import json
import sys
import datetime
import shutil
import hashlib
import threading
from document_processor import SUPPORTED_EXTENSIONS, extract_text, get_document_chunks
from vector_store import (
    get_documents_save_dir,
    rebuild_vector_store,
    add_documents_to_store,
    clear_vector_store_cache,
    VECTOR_STORE_DIR
)

METADATA_PATH = os.path.join(VECTOR_STORE_DIR, "metadata.json")

# Reentrant lock to prevent race conditions during concurrent indexing/deleting
db_lock = threading.RLock()


def load_metadata() -> dict:
    """
    Loads document metadata from the JSON persistence file.
    """
    if os.path.exists(METADATA_PATH):
        try:
            with open(METADATA_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading metadata.json: {e}")
    
    return {
        "files": {},
        "watch_folders": [],
        "watched_sources": {},
        "total_chunks": 0,
        "total_embeddings": 0
    }


def save_metadata(metadata: dict):
    """
    Persists document metadata to the JSON file.
    """
    os.makedirs(VECTOR_STORE_DIR, exist_ok=True)
    try:
        with open(METADATA_PATH, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)
    except Exception as e:
        print(f"Error saving metadata: {e}")


def get_watch_folders() -> list[str]:
    """Return configured local folders monitored for automatic KB updates."""
    metadata = load_metadata()
    folders = metadata.get("watch_folders", [])
    return [f for f in folders if isinstance(f, str) and f.strip()]


def set_watch_folders(folders: list[str]) -> None:
    """Persist normalized watch-folder paths."""
    metadata = load_metadata()
    normalized = []
    for folder in folders:
        folder = folder.strip().strip('"')
        if not folder:
            continue
        abs_folder = os.path.abspath(os.path.expanduser(folder))
        if abs_folder not in normalized:
            normalized.append(abs_folder)
    metadata["watch_folders"] = normalized
    metadata.setdefault("watched_sources", {})
    save_metadata(metadata)


def _is_supported_file(path: str) -> bool:
    ext = os.path.splitext(path)[1].lstrip(".").lower()
    return ext in SUPPORTED_EXTENSIONS


def _watched_doc_name(source_path: str) -> str:
    abs_path = os.path.abspath(source_path)
    drive, tail = os.path.splitdrive(abs_path)
    slug = (drive.replace(":", "") + tail).strip("\\/")
    slug = "".join(c if c.isalnum() else "_" for c in slug)
    return f"watched__{slug}"


def sync_watch_folders() -> bool:
    """
    Copy new/modified supported files from configured watch folders into the
    persisted documents directory, then let the normal incremental sync update FAISS.
    """
    metadata = load_metadata()
    watch_folders = metadata.get("watch_folders", [])
    watched_sources = metadata.setdefault("watched_sources", {})
    save_dir = get_documents_save_dir()
    changed = False

    current_sources = {}
    for folder in watch_folders:
        if not os.path.isdir(folder):
            print(f"Watch folder unavailable: {folder}")
            continue
        for root, _, files in os.walk(folder):
            for filename in files:
                source_path = os.path.abspath(os.path.join(root, filename))
                if not _is_supported_file(source_path):
                    continue
                stat = os.stat(source_path)
                imported_name = _watched_doc_name(source_path)
                imported_path = os.path.join(save_dir, imported_name)
                current_sources[source_path] = imported_name
                previous = watched_sources.get(source_path, {})
                if (
                    previous.get("mtime") != stat.st_mtime
                    or previous.get("size_bytes") != stat.st_size
                    or not os.path.exists(imported_path)
                ):
                    shutil.copy2(source_path, imported_path)
                    watched_sources[source_path] = {
                        "imported_name": imported_name,
                        "mtime": stat.st_mtime,
                        "size_bytes": stat.st_size,
                    }
                    changed = True

    for source_path, previous in list(watched_sources.items()):
        if source_path not in current_sources:
            imported_name = previous.get("imported_name")
            if imported_name:
                imported_path = os.path.join(save_dir, imported_name)
                if os.path.exists(imported_path):
                    os.remove(imported_path)
                    changed = True
            del watched_sources[source_path]

    if changed:
        metadata["watched_sources"] = watched_sources
        save_metadata(metadata)
    return changed


def add_document(filename: str, file_data: bytes) -> tuple[bool, str]:
    """
    Saves a raw file to the vector store documents directory and updates the
    FAISS index incrementally when possible. Includes SHA256 duplicate content detection.
    """
    with db_lock:
        try:
            filename = os.path.basename(filename)
            save_dir = get_documents_save_dir()
            file_path = os.path.join(save_dir, filename)

            # 1. Duplicate detection: calculate SHA256 hash
            file_hash = hashlib.sha256(file_data).hexdigest()
            metadata = load_metadata()
            meta_files = metadata.setdefault("files", {})

            for existing_name, info in meta_files.items():
                if info.get("hash") == file_hash:
                    if existing_name != filename:
                        return False, f"Duplicate document detected: content is identical to '{existing_name}'."
                    else:
                        return True, "Document is already indexed and up-to-date."

            # 2. Save raw file to disk
            with open(file_path, "wb") as f:
                f.write(file_data)

            # 3. Validate that the new file can actually be extracted before indexing.
            try:
                text = extract_text(file_path, filename)
            except Exception as extract_err:
                raise RuntimeError(f"Text extraction failed: {extract_err}")

            chunks = get_document_chunks(text, filename)
            if not chunks:
                raise ValueError("No readable text could be extracted from this document format.")

            existing_file = meta_files.get(filename)
            is_modified = False
            if existing_file:
                new_size = os.path.getsize(file_path)
                new_mtime = os.path.getmtime(file_path)
                if abs(new_mtime - existing_file.get("mtime", 0)) > 1.0 or new_size != existing_file.get("size_bytes", 0):
                    is_modified = True

            if is_modified:
                print(f"Document '{filename}' changed, rebuilding full index...", file=sys.stderr)
                result = rebuild_knowledge_base()
                if not result:
                    raise RuntimeError("Knowledge base rebuild failed after saving the updated document.")
                msg = f"Document updated and knowledge base rebuilt successfully ({len(chunks)} chunks)."
            else:
                # 4. Incrementally add a newly uploaded file to the vector store.
                db = add_documents_to_store(chunks)
                if db is None:
                    raise RuntimeError("Failed to create or load the vector store FAISS index.")

                metadata["total_chunks"] = metadata.get("total_chunks", 0) + len(chunks)
                metadata["total_embeddings"] = metadata.get("total_embeddings", 0) + len(chunks)
                meta_files[filename] = {
                    "size_bytes": os.path.getsize(file_path),
                    "mtime": os.path.getmtime(file_path),
                    "chunks_count": len(chunks),
                    "hash": file_hash,
                    "added_at": datetime.datetime.fromtimestamp(os.path.getctime(file_path)).isoformat()
                }
                save_metadata(metadata)
                msg = f"Document indexed successfully ({len(chunks)} chunks)."

            clear_vector_store_cache()
            return True, msg
        except Exception as e:
            print(f"Error adding document '{filename}': {e}")
            if 'file_path' in locals() and os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    pass
            return False, str(e)


def delete_document(filename: str) -> bool:
    """
    Deletes a document raw file, removes it from metadata, and rebuilds the FAISS index.
    """
    with db_lock:
        try:
            save_dir = get_documents_save_dir()
            file_path = os.path.join(save_dir, filename)

            # 1. Remove raw file from disk
            if os.path.exists(file_path):
                os.remove(file_path)

            # 2. Remove from metadata
            metadata = load_metadata()
            if filename in metadata["files"]:
                del metadata["files"][filename]

            save_metadata(metadata)

            # 3. Rebuild vector store from remaining files
            rebuild_knowledge_base()
            
            clear_vector_store_cache()
            return True
        except Exception as e:
            print(f"Error deleting document '{filename}': {e}")
            return False


def rebuild_knowledge_base() -> bool:
    """
    Forces a full rebuild of the FAISS vector index using the raw files currently
    stored on disk inside `./vector_store/documents/`.
    Parallelizes file text extraction using a ThreadPoolExecutor.
    """
    with db_lock:
        try:
            save_dir = get_documents_save_dir()
            files = [f for f in os.listdir(save_dir) if os.path.isfile(os.path.join(save_dir, f))]

            all_chunks = []
            existing_metadata = load_metadata()
            metadata = {
                "files": {},
                "watch_folders": existing_metadata.get("watch_folders", []),
                "watched_sources": existing_metadata.get("watched_sources", {}),
                "total_chunks": 0,
                "total_embeddings": 0
            }

            if files:
                from concurrent.futures import ThreadPoolExecutor

                def process_file(filename: str):
                    file_path = os.path.join(save_dir, filename)
                    try:
                        with open(file_path, "rb") as f:
                            content_bytes = f.read()
                        file_hash = hashlib.sha256(content_bytes).hexdigest()
                        
                        text = extract_text(file_path, filename)
                        chunks = get_document_chunks(text, filename)
                        meta = {
                            "size_bytes": os.path.getsize(file_path),
                            "mtime": os.path.getmtime(file_path),
                            "chunks_count": len(chunks),
                            "hash": file_hash,
                            "added_at": datetime.datetime.fromtimestamp(os.path.getctime(file_path)).isoformat()
                        }
                        return filename, chunks, meta, None
                    except Exception as file_err:
                        return filename, [], {}, str(file_err)

                max_workers = min(4, len(files))
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    results = list(executor.map(process_file, files))

                for filename, chunks, meta, err in results:
                    if err:
                        print(f"Error indexing {filename} during rebuild: {err}", file=sys.stderr)
                    else:
                        all_chunks.extend(chunks)
                        metadata["files"][filename] = meta

            # Recompute totals
            metadata["total_chunks"] = len(all_chunks)
            metadata["total_embeddings"] = len(all_chunks)

            # Rebuild FAISS index
            rebuild_vector_store(all_chunks)
            save_metadata(metadata)
            
            clear_vector_store_cache()
            return True
        except Exception as e:
            print(f"Failed to rebuild knowledge base: {e}")
            return False


def sync_and_refresh_knowledge_base() -> bool:
    """
    Scans the documents directory and compares file sizes/modification times
    with metadata.json. Performs incremental indexing (only new/updated files)
    and removes vectors of deleted/modified files without rebuilding the entire index.

    Returns:
        bool: True if a refresh/sync was executed and changes were made, False if already in sync.
    """
    with db_lock:
        save_dir = get_documents_save_dir()
        sync_watch_folders()
        
        if not os.path.exists(save_dir):
            return False

        fs_files = {
            f: {
                "size": os.path.getsize(os.path.join(save_dir, f)),
                "mtime": os.path.getmtime(os.path.join(save_dir, f))
            }
            for f in os.listdir(save_dir)
            if os.path.isfile(os.path.join(save_dir, f))
        }

        metadata = load_metadata()
        meta_files = metadata.setdefault("files", {})

        files_added = []
        files_modified = []
        files_deleted = []

        for filename, info in fs_files.items():
            if filename not in meta_files:
                files_added.append(filename)
            else:
                meta_info = meta_files[filename]
                if abs(info["mtime"] - meta_info.get("mtime", 0)) > 1.0 or info["size"] != meta_info.get("size_bytes", 0):
                    files_modified.append(filename)

        for filename in list(meta_files.keys()):
            if filename not in fs_files:
                files_deleted.append(filename)

        if not files_added and not files_modified and not files_deleted:
            return False

        print(f"Incremental Sync: added={files_added}, modified={files_modified}, deleted={files_deleted}", file=sys.stderr)

        # If files were modified or deleted, rebuild the index for correctness.
        if files_modified or files_deleted:
            return rebuild_knowledge_base()

        # Only new files were added; add them incrementally.
        all_new_chunks = []
        for filename in files_added:
            file_path = os.path.join(save_dir, filename)
            try:
                with open(file_path, "rb") as f:
                    content_bytes = f.read()
                file_hash = hashlib.sha256(content_bytes).hexdigest()
                
                # Check for duplicate in existing files during sync
                duplicate = False
                for existing_name, info in meta_files.items():
                    if info.get("hash") == file_hash:
                        print(f"Sync duplicate detected: {filename} matches {existing_name}", file=sys.stderr)
                        duplicate = True
                        break
                if duplicate:
                    os.remove(file_path)
                    continue

                text = extract_text(file_path, filename)
                chunks = get_document_chunks(text, filename)
                if not chunks:
                    raise ValueError(f"No readable text extracted from '{filename}'.")
                all_new_chunks.extend(chunks)
                meta_files[filename] = {
                    "size_bytes": fs_files[filename]["size"],
                    "mtime": fs_files[filename]["mtime"],
                    "chunks_count": len(chunks),
                    "hash": file_hash,
                    "added_at": datetime.datetime.fromtimestamp(os.path.getctime(file_path)).isoformat()
                }
            except Exception as e:
                print(f"Error indexing {filename} incrementally: {e}", file=sys.stderr)

        if all_new_chunks:
            print(f"Incremental sync: Adding {len(all_new_chunks)} new chunks to FAISS...", file=sys.stderr)
            add_documents_to_store(all_new_chunks)

        total_chunks = sum(info.get("chunks_count", 0) for info in meta_files.values())
        metadata["total_chunks"] = total_chunks
        metadata["total_embeddings"] = total_chunks

        save_metadata(metadata)
        clear_vector_store_cache()
        return True


# ---------------------------------------------------------------------------
# Background Scheduler
# ---------------------------------------------------------------------------
_scheduler_started = False
_scheduler_lock = threading.Lock()

def start_background_scheduler():
    """Starts the background scheduler thread to check watched folders periodically."""
    global _scheduler_started
    with _scheduler_lock:
        if _scheduler_started:
            return
        _scheduler_started = True
        
    def worker():
        import time
        print("[Scheduler] Background scheduler thread started.", file=sys.stderr)
        while True:
            try:
                time.sleep(30)
                metadata = load_metadata()
                watch_folders = metadata.get("watch_folders", [])
                if watch_folders:
                    # Call sync using our reentrant lock
                    changed = sync_and_refresh_knowledge_base()
                    if changed:
                        print("[Scheduler] Automatic watch-folder sync complete.", file=sys.stderr)
            except Exception as e:
                print(f"[Scheduler Error] Background sync failed: {e}", file=sys.stderr)
                
    t = threading.Thread(target=worker, daemon=True, name="KB_Background_Scheduler")
    t.start()

# Start background thread automatically when this module is imported
start_background_scheduler()
