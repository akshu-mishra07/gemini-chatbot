from __future__ import annotations

"""Local authentication and profile management.

This intentionally uses only the Python standard library so the project does
not require an external identity provider for internship/demo deployments.
"""

import hashlib
import hmac
import os
from typing import Any

from database.storage import execute, fetch_one, now_iso


PBKDF2_ITERATIONS = 260_000


def _hash_password(password: str, salt: bytes) -> str:
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS,
    )
    return digest.hex()


def create_user(
    username: str,
    password: str,
    display_name: str | None = None,
    preferred_language: str = "en",
) -> tuple[bool, str]:
    username = username.strip().lower()
    display_name = (display_name or username).strip()
    if len(username) < 3:
        return False, "Username must be at least 3 characters."
    if len(password) < 8:
        return False, "Password must be at least 8 characters."

    salt = os.urandom(16)
    password_hash = _hash_password(password, salt)
    try:
        execute(
            """
            INSERT INTO users
                (username, password_hash, salt, display_name, preferred_language, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (username, password_hash, salt.hex(), display_name, preferred_language, now_iso()),
        )
        return True, "Account created."
    except Exception as exc:
        if "UNIQUE" in str(exc).upper():
            return False, "That username already exists."
        return False, f"Could not create account: {exc}"


def authenticate_user(username: str, password: str) -> dict[str, Any] | None:
    username = username.strip().lower()
    row = fetch_one("SELECT * FROM users WHERE username = ?", (username,))
    if not row:
        return None

    expected = row["password_hash"]
    actual = _hash_password(password, bytes.fromhex(row["salt"]))
    if not hmac.compare_digest(expected, actual):
        return None

    execute("UPDATE users SET last_login = ? WHERE id = ?", (now_iso(), row["id"]))
    row.pop("password_hash", None)
    row.pop("salt", None)
    return row


def get_user_profile(user_id: int | str | None) -> dict[str, Any] | None:
    if not user_id:
        return None
    row = fetch_one(
        """
        SELECT id, username, display_name, role, preferred_language, theme, created_at, last_login
        FROM users WHERE id = ?
        """,
        (user_id,),
    )
    return row


def update_user_profile(
    user_id: int | str,
    *,
    display_name: str,
    role: str,
    preferred_language: str,
    theme: str,
) -> bool:
    execute(
        """
        UPDATE users
        SET display_name = ?, role = ?, preferred_language = ?, theme = ?
        WHERE id = ?
        """,
        (
            display_name.strip() or "OmniChat User",
            role.strip() or "Customer Support Agent",
            preferred_language,
            theme,
            user_id,
        ),
    )
    return True


def guest_profile() -> dict[str, Any]:
    return {
        "id": "guest",
        "username": "guest",
        "display_name": "Guest",
        "role": "Customer Support Agent",
        "preferred_language": "en",
        "theme": "Dark",
    }

