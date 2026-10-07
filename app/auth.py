"""API-key authentication.  >>> YOU implement the TODOs in this file. <<<

THE BIG IDEA (read this first)
------------------------------
Right now anyone who finds our URL can call /ask and spend OUR Azure money.
API-key auth fixes that: every request must carry a secret "key" in a header:

    X-API-Key: rk_AbC123...

The server checks the key. Valid -> request continues. Missing/wrong -> HTTP 401.

THE ONE RULE: NEVER STORE THE RAW KEY
-------------------------------------
If our database leaks and it holds raw keys, every key is stolen.
So we store only a HASH of each key. A hash is a one-way scrambler:

    hash("rk_AbC123")  ->  "9f86d081884c7d65..."   (always the same output for the same input)

You can't turn the hash back into the key, but you CAN check a key someone sends us:
hash what they sent, and see if that hash is in our table.

THE FLOW
--------
  1. Admin runs `python -m scripts.create_key alice`
        -> create_key("alice") makes a random key, stores its hash, returns the raw key ONCE.
  2. Alice sends requests with header  X-API-Key: <raw key>
  3. FastAPI runs require_api_key() before our endpoint (that's what `Depends` does).
        -> hash the header value, look it up -> OK, or raise HTTPException(401).

Work through the functions in this order. After each one, run:
    pytest tests/test_auth.py -q
and watch more tests turn green.
"""
import hashlib
import secrets
import sqlite3

from fastapi import Header, HTTPException

from app.config import settings

KEY_PREFIX = "rk_"  # a visible prefix makes leaked keys easy to recognise and search for


def _conn() -> sqlite3.Connection:
    """BOILERPLATE (already done): open the SQLite file and make sure the table exists.

    The table stores the HASH of each key (key_hash), never the key itself.
    `is_active` lets us switch a key off later without deleting its history.
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


# --------------------------------------------------------------------------- step 1
def generate_key() -> str:
    """Make a new random key like 'rk_Qm9...'.

    TODO 1:
      - Use secrets.token_urlsafe(32) to get 32 random bytes as URL-safe text.
        (Use `secrets`, NOT `random`: `random` is predictable, `secrets` is meant for passwords/keys.)
      - Put KEY_PREFIX in front and return it.
    """
    raise NotImplementedError("TODO 1: implement generate_key")


# --------------------------------------------------------------------------- step 2
def hash_key(raw_key: str) -> str:
    """Return the SHA-256 hash of a key as a 64-character hex string.

    TODO 2:
      - hashlib.sha256(...) wants BYTES, not text. Turn text into bytes with raw_key.encode().
      - .hexdigest() turns the result into a readable hex string.
      - Same input must always give the same output (the tests check this).

    (Why SHA-256 and not a slow password hash like bcrypt? Our keys are long and random,
     so they can't be guessed by brute force. Passwords chosen by humans are different -
     they need slow hashes. Good thing to be able to explain in an interview.)
    """
    raise NotImplementedError("TODO 2: implement hash_key")


# --------------------------------------------------------------------------- step 3
def create_key(name: str) -> str:
    """Create a key for `name`, store its HASH, and return the RAW key (shown once!).

    TODO 3:
      - raw = generate_key()
      - Insert (name, hash_key(raw)) into the api_keys table.
        Use a `with _conn() as conn:` block (it saves the change when the block ends)
        and a parameterized query:
            conn.execute("INSERT INTO api_keys (name, key_hash) VALUES (?, ?)", (name, ...))
        The `?` placeholders matter: NEVER build SQL by gluing strings together
        (that's how SQL-injection attacks work).
      - return raw   <- the only moment anyone ever sees the raw key.
    """
    raise NotImplementedError("TODO 3: implement create_key")


# --------------------------------------------------------------------------- step 4
def verify_key(raw_key: str) -> str | None:
    """Return the key owner's NAME if the key is valid and active, otherwise None.

    TODO 4:
      - If raw_key is empty/None, return None straight away.
      - Hash it, then look for that hash:
            conn.execute("SELECT name FROM api_keys WHERE key_hash = ? AND is_active = 1", (...,))
        `.fetchone()` gives one row (a tuple like ("alice",)) or None if nothing matched.
      - Return row[0] if found, else None.
    """
    raise NotImplementedError("TODO 4: implement verify_key")


# --------------------------------------------------------------------------- step 5
def require_api_key(x_api_key: str | None = Header(default=None)) -> str:
    """FastAPI DEPENDENCY: runs before an endpoint and either lets the request through or stops it.

    Note: FastAPI turns the argument name `x_api_key` into the header name `X-API-Key`
    automatically (underscores become hyphens, case doesn't matter).

    TODO 5:
      - owner = verify_key(x_api_key)
      - If owner is None: raise HTTPException(status_code=401, detail="Invalid or missing API key")
        Use the SAME message for "missing" and "wrong" key, so an attacker learns nothing
        about which keys exist.
      - Otherwise return owner (endpoints can use it to know who is calling - handy for
        per-user rate limits and usage logs later).
    """
    raise NotImplementedError("TODO 5: implement require_api_key")


# --------------------------------------------------------------------------- stretch
def revoke_key(name: str) -> int:
    """STRETCH GOAL (do it after everything else is green).

    Switch off every key belonging to `name` (set is_active = 0) and return how many rows
    changed (cursor.rowcount). Then remove the @pytest.mark.skip line from
    test_revoked_key_is_rejected in tests/test_auth.py.
    """
    raise NotImplementedError("STRETCH: implement revoke_key")
