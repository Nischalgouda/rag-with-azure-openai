"""API-key authentication.

THE IDEA
--------
Every request may carry a secret key in a header:   X-API-Key: rk_AbC123...
The server never stores the raw key, only its SHA-256 hash. If the database leaks, the hashes
cannot be turned back into usable keys. To check a request we hash what it sent and look for
that hash in the table.

FLOW
----
1. An admin runs `python -m scripts.create_key alice` -> create_key("alice") stores the hash and
   returns the raw key exactly once.
2. Alice sends the key in X-API-Key.
3. FastAPI runs a dependency from this module before the endpoint:
   - require_api_key: key required (401 otherwise)
   - optional_api_key: no key is fine (anonymous), but a key that is present must be valid
"""
import hashlib
import secrets
import sqlite3

from fastapi import Header, HTTPException

from app.config import settings

KEY_PREFIX = "rk_"  # a visible prefix makes leaked keys easy to recognise and search for


def _conn() -> sqlite3.Connection:
    """Open the SQLite file and make sure the table exists.

    The table stores the HASH of each key (key_hash), never the key itself.
    `is_active` lets us switch a key off without deleting its history.
    """
    conn = sqlite3.connect(settings.db_path)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS api_keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            key_hash TEXT NOT NULL UNIQUE,
            is_active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP)"""
    )
    return conn


def generate_key() -> str:
    """A new random key like 'rk_Qm9...'. Uses `secrets` (a cryptographically secure source)."""
    return KEY_PREFIX + secrets.token_urlsafe(32)


def hash_key(raw_key: str) -> str:
    """SHA-256 of the key as 64 hex characters. Deterministic: same key, same hash.

    A fast hash is appropriate here because API keys are long and random, so they cannot be
    guessed by brute force. Human-chosen passwords are different and need slow hashes (bcrypt, argon2).
    """
    return hashlib.sha256(raw_key.encode()).hexdigest()


def create_key(name: str) -> str:
    """Create a key for `name`, store its hash, return the raw key (shown once)."""
    raw = generate_key()
    with _conn() as conn:
        # Placeholders (?) keep user input out of the SQL text, which prevents SQL injection.
        conn.execute("INSERT INTO api_keys (name, key_hash) VALUES (?, ?)", (name, hash_key(raw)))
    return raw


def verify_key(raw_key: str | None) -> str | None:
    """The key owner's name if the key is valid and active, otherwise None."""
    if not raw_key:
        return None
    with _conn() as conn:
        row = conn.execute(
            "SELECT name FROM api_keys WHERE key_hash = ? AND is_active = 1",
            (hash_key(raw_key),),
        ).fetchone()
    return row[0] if row else None


def revoke_key(name: str) -> int:
    """Deactivate every key belonging to `name`. Returns how many keys were switched off."""
    with _conn() as conn:
        cursor = conn.execute("UPDATE api_keys SET is_active = 0 WHERE name = ? AND is_active = 1", (name,))
        return cursor.rowcount


_UNAUTHORIZED = "Invalid or missing API key"  # one message for 'missing' and 'wrong': reveals nothing


def require_api_key(x_api_key: str | None = Header(default=None)) -> str:
    """FastAPI dependency: the request must carry a valid key. Returns the owner's name."""
    owner = verify_key(x_api_key)
    if owner is None:
        raise HTTPException(status_code=401, detail=_UNAUTHORIZED)
    return owner


def optional_api_key(x_api_key: str | None = Header(default=None)) -> str | None:
    """FastAPI dependency: anonymous is allowed, but a key that is sent must be valid."""
    if not x_api_key:
        return None
    return require_api_key(x_api_key)
