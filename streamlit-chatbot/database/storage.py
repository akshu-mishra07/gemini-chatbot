from __future__ import annotations

"""SQLite persistence helpers for OmniChat.

SQLite stores local profiles, sentiment events, image OCR history,
translation memory, and lightweight analytics.
"""

import datetime as dt
import os
import sqlite3
from collections.abc import Iterable
from typing import Any


DB_PATH = os.environ.get("OMNICHAT_DB_PATH", os.path.join("database", "omnichat.db"))


def _now() -> str:
    return dt.datetime.now().isoformat(timespec="seconds")


def _connect() -> sqlite3.Connection:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def initialize_database() -> None:
    """Create all application tables if they do not already exist."""
    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                salt TEXT NOT NULL,
                display_name TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'Customer Support Agent',
                preferred_language TEXT NOT NULL DEFAULT 'en',
                theme TEXT NOT NULL DEFAULT 'Dark',
                created_at TEXT NOT NULL,
                last_login TEXT
            );

            CREATE TABLE IF NOT EXISTS sentiment_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                session_id TEXT,
                label TEXT NOT NULL,
                emotion TEXT, -- Task 5: Emotion classification
                confidence REAL NOT NULL,
                message TEXT NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS image_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                session_id TEXT,
                filename TEXT NOT NULL,
                path TEXT NOT NULL,
                width INTEGER,
                height INTEGER,
                ocr_text TEXT,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS research_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                query TEXT NOT NULL,
                result_count INTEGER NOT NULL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS translation_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_text TEXT NOT NULL,
                source_lang TEXT NOT NULL,
                target_lang TEXT NOT NULL,
                translated_text TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(source_text, source_lang, target_lang)
            );

            CREATE TABLE IF NOT EXISTS generated_images_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                original_prompt TEXT NOT NULL,
                enhanced_prompt TEXT NOT NULL,
                detected_entities TEXT NOT NULL,
                style TEXT NOT NULL,
                provider TEXT NOT NULL,
                filepath TEXT NOT NULL,
                aspect_ratio TEXT NOT NULL,
                generation_time REAL NOT NULL,
                created_at TEXT NOT NULL
            );
            """
        )
        
        # Add emotion column to existing sentiment_events table if missing (migration)
        try:
            conn.execute("ALTER TABLE sentiment_events ADD COLUMN emotion TEXT")
            conn.commit()
        except sqlite3.OperationalError:
            pass  # Already exists


def execute(sql: str, params: Iterable[Any] = ()) -> int:
    initialize_database()
    with _connect() as conn:
        cursor = conn.execute(sql, tuple(params))
        conn.commit()
        return int(cursor.lastrowid or 0)


def fetch_one(sql: str, params: Iterable[Any] = ()) -> dict[str, Any] | None:
    initialize_database()
    with _connect() as conn:
        row = conn.execute(sql, tuple(params)).fetchone()
    return dict(row) if row else None


def fetch_all(sql: str, params: Iterable[Any] = ()) -> list[dict[str, Any]]:
    initialize_database()
    with _connect() as conn:
        rows = conn.execute(sql, tuple(params)).fetchall()
    return [dict(row) for row in rows]


def now_iso() -> str:
    return _now()


# --- Translation Memory Helpers ---

def get_cached_translation(text: str, source_lang: str, target_lang: str) -> str | None:
    """Check translation cache for matching translation."""
    try:
        row = fetch_one(
            "SELECT translated_text FROM translation_memory WHERE source_text = ? AND source_lang = ? AND target_lang = ?",
            (text, source_lang, target_lang)
        )
        return row["translated_text"] if row else None
    except Exception:
        return None


def set_cached_translation(text: str, source_lang: str, target_lang: str, translated: str):
    """Insert or replace translation in translation memory cache."""
    try:
        execute(
            "INSERT OR REPLACE INTO translation_memory (source_text, source_lang, target_lang, translated_text, created_at) VALUES (?, ?, ?, ?, ?)",
            (text, source_lang, target_lang, translated, now_iso())
        )
    except Exception as e:
        import sys
        print(f"[Storage Error] Failed to cache translation: {e}", file=sys.stderr)


# --- Generated Images History Helpers ---

def record_image_generation_history(result: dict) -> None:
    import json
    entities_json = json.dumps(result.get("entities", []))
    execute(
        """
        INSERT INTO generated_images_history
            (original_prompt, enhanced_prompt, detected_entities, style, provider, filepath, aspect_ratio, generation_time, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            result.get("original_prompt", ""),
            result.get("enhanced_prompt", ""),
            entities_json,
            result.get("style", "Photorealistic"),
            result.get("provider", "None"),
            result.get("image_path") or result.get("filepath") or "",
            result.get("aspect_ratio", "1:1"),
            result.get("generation_time_sec", 0.0),
            now_iso()
        )
    )


def list_image_generation_history(limit: int = 100) -> list[dict[str, Any]]:
    import json
    rows = fetch_all(
        "SELECT * FROM generated_images_history ORDER BY created_at DESC LIMIT ?",
        (limit,)
    )
    results = []
    for r in rows:
        row_dict = dict(r)
        try:
            row_dict["entities"] = json.loads(row_dict["detected_entities"])
        except Exception:
            row_dict["entities"] = []
        results.append(row_dict)
    return results
