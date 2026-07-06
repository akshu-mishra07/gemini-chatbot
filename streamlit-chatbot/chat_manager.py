"""
chat_manager.py - Persistent chat session storage and export helpers.
"""

from __future__ import annotations

import datetime as _dt
import json
import os
import re
import uuid

CHAT_DIR = "./chat_sessions"


def _now() -> str:
    return _dt.datetime.now().isoformat(timespec="seconds")


def _safe_id(session_id: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_-]", "_", session_id)


def _session_path(session_id: str) -> str:
    os.makedirs(CHAT_DIR, exist_ok=True)
    return os.path.join(CHAT_DIR, f"{_safe_id(session_id)}.json")


def list_sessions() -> list[dict]:
    os.makedirs(CHAT_DIR, exist_ok=True)
    sessions = []
    for filename in os.listdir(CHAT_DIR):
        if not filename.endswith(".json"):
            continue
        try:
            with open(os.path.join(CHAT_DIR, filename), "r", encoding="utf-8") as f:
                payload = json.load(f)
            sessions.append(
                {
                    "id": payload.get("id", filename[:-5]),
                    "title": payload.get("title", "Untitled chat"),
                    "mode": payload.get("mode", "General Assistant"),
                    "updated_at": payload.get("updated_at", ""),
                    "created_at": payload.get("created_at", ""),
                }
            )
        except Exception as exc:
            print(f"[Chat Sessions] Failed to read {filename}: {exc}")
    sessions.sort(key=lambda item: item.get("updated_at", ""), reverse=True)
    return sessions


def create_session(mode: str = "General Assistant", title: str = "New chat") -> dict:
    session_id = uuid.uuid4().hex
    payload = {
        "id": session_id,
        "title": title,
        "mode": mode,
        "messages": [],
        "gemini_history": [],
        "created_at": _now(),
        "updated_at": _now(),
    }
    save_session(payload)
    return payload


def load_session(session_id: str) -> dict | None:
    path = _session_path(session_id)
    if not os.path.exists(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        print(f"[Chat Sessions] Failed to load {session_id}: {exc}")
        return None


def save_session(payload: dict) -> None:
    payload.setdefault("id", uuid.uuid4().hex)
    payload.setdefault("created_at", _now())
    payload["updated_at"] = _now()
    path = _session_path(payload["id"])
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


def update_session(session_id: str, *, mode: str, messages: list, gemini_history: list) -> None:
    payload = load_session(session_id) or create_session(mode=mode)
    payload["mode"] = mode
    payload["messages"] = messages
    payload["gemini_history"] = gemini_history
    if payload.get("title", "New chat") == "New chat":
        first_user = next((m.get("content", "") for m in messages if m.get("role") == "user"), "")
        if first_user:
            payload["title"] = first_user[:50]
    save_session(payload)


def rename_session(session_id: str, title: str) -> bool:
    payload = load_session(session_id)
    if not payload:
        return False
    payload["title"] = title.strip() or "Untitled chat"
    save_session(payload)
    return True


def delete_session(session_id: str) -> bool:
    path = _session_path(session_id)
    try:
        if os.path.exists(path):
            os.remove(path)
        return True
    except Exception as exc:
        print(f"[Chat Sessions] Failed to delete {session_id}: {exc}")
        return False


def export_chat_txt(messages: list[dict]) -> str:
    lines = []
    for msg in messages:
        role = msg.get("role", "unknown").upper()
        content = msg.get("content", "")
        lines.append(f"[{role}]\n{content}\n")
    return "\n".join(lines)


def _pdf_escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def export_chat_pdf(messages: list[dict]) -> bytes:
    # Minimal single-font PDF writer. It keeps exports dependency-free.
    text = export_chat_txt(messages)
    clean = text.encode("latin-1", errors="replace").decode("latin-1")
    lines = []
    for raw_line in clean.splitlines():
        while len(raw_line) > 92:
            lines.append(raw_line[:92])
            raw_line = raw_line[92:]
        lines.append(raw_line)

    pages = [lines[i:i + 46] for i in range(0, len(lines), 46)] or [[]]
    objects = ["<< /Type /Catalog /Pages 2 0 R >>"]
    kids = []
    for page_idx, page_lines in enumerate(pages):
        page_obj = 3 + page_idx * 2
        content_obj = page_obj + 1
        kids.append(f"{page_obj} 0 R")
        y = 760
        stream_lines = ["BT", "/F1 10 Tf"]
        first_line = True
        for line in page_lines:
            if first_line:
                stream_lines.append(f"72 {y} Td ({_pdf_escape(line)}) Tj")
                first_line = False
            else:
                stream_lines.append(f"0 -14 Td ({_pdf_escape(line)}) Tj")
        stream_lines.append("ET")
        stream = "\n".join(stream_lines)
        objects.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Resources << /Font << /F1 {3 + len(pages) * 2} 0 R >> >> "
            f"/Contents {content_obj} 0 R >>"
        )
        objects.append(f"<< /Length {len(stream.encode('latin-1'))} >>\nstream\n{stream}\nendstream")
    objects.insert(1, f"<< /Type /Pages /Kids [{' '.join(kids)}] /Count {len(pages)} >>")
    objects.append("<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    chunks = ["%PDF-1.4\n"]
    offsets = [0]
    for idx, obj in enumerate(objects, 1):
        offsets.append(sum(len(c.encode("latin-1")) for c in chunks))
        chunks.append(f"{idx} 0 obj\n{obj}\nendobj\n")
    xref_start = sum(len(c.encode("latin-1")) for c in chunks)
    chunks.append(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n")
    for offset in offsets[1:]:
        chunks.append(f"{offset:010d} 00000 n \n")
    chunks.append(f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_start}\n%%EOF")
    return "".join(chunks).encode("latin-1")
