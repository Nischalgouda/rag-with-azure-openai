"""Tests for app/auth.py. They are written FIRST on purpose ("test-first"):
they FAIL now, and your job is to make them pass.   Run:  pytest tests/test_auth.py -q

Read each test: it is the spec. A test says "given this input, I expect this output".
"""
import sqlite3

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app import auth
from app.config import settings


@pytest.fixture(autouse=True)
def temp_db(tmp_path, monkeypatch):
    """Every test gets its own empty database file, so tests never affect each other
    (and never touch your real usage.db)."""
    monkeypatch.setattr(settings, "db_path", str(tmp_path / "test.db"))


@pytest.fixture()
def client():
    """A tiny app with ONE protected route, just for testing the dependency in isolation."""
    app = FastAPI()

    @app.get("/protected")
    def protected(owner: str = Depends(auth.require_api_key)):
        return {"owner": owner}

    return TestClient(app)


# ----- TODO 1: generate_key ------------------------------------------------------------
def test_generated_keys_have_prefix_and_are_unique():
    a, b = auth.generate_key(), auth.generate_key()
    assert a.startswith("rk_") and b.startswith("rk_")
    assert a != b            # random, so two keys must differ
    assert len(a) > 30       # long enough to be unguessable


# ----- TODO 2: hash_key ----------------------------------------------------------------
def test_hash_is_deterministic_and_not_the_plaintext():
    assert auth.hash_key("abc") == auth.hash_key("abc")   # same input -> same output
    assert auth.hash_key("abc") != auth.hash_key("abd")   # different input -> different output
    assert auth.hash_key("abc") != "abc"
    assert len(auth.hash_key("abc")) == 64                # SHA-256 as hex is 64 characters


# ----- TODO 3: create_key --------------------------------------------------------------
def test_create_key_stores_only_the_hash():
    raw = auth.create_key("alice")
    rows = sqlite3.connect(settings.db_path).execute("SELECT * FROM api_keys").fetchall()
    assert len(rows) == 1
    assert raw not in str(rows)                 # the raw key must NOT be in the database
    assert auth.hash_key(raw) in str(rows)      # only its hash is


# ----- TODO 4: verify_key --------------------------------------------------------------
def test_verify_key_returns_owner_for_valid_key():
    raw = auth.create_key("alice")
    assert auth.verify_key(raw) == "alice"


def test_verify_key_rejects_wrong_empty_and_none():
    auth.create_key("alice")
    assert auth.verify_key("rk_not-a-real-key") is None
    assert auth.verify_key("") is None
    assert auth.verify_key(None) is None


# ----- TODO 5: require_api_key (the real FastAPI behaviour) ------------------------------
def test_request_without_key_is_401(client):
    assert client.get("/protected").status_code == 401


def test_request_with_wrong_key_is_401(client):
    auth.create_key("alice")
    assert client.get("/protected", headers={"X-API-Key": "rk_wrong"}).status_code == 401


def test_request_with_valid_key_is_allowed_and_knows_the_owner(client):
    raw = auth.create_key("alice")
    r = client.get("/protected", headers={"X-API-Key": raw})
    assert r.status_code == 200
    assert r.json() == {"owner": "alice"}


def test_missing_and_wrong_key_give_the_same_error_message(client):
    # Security: the error must not reveal whether a key exists.
    missing = client.get("/protected").json()
    wrong = client.get("/protected", headers={"X-API-Key": "rk_wrong"}).json()
    assert missing == wrong


# ----- STRETCH: revoke_key -------------------------------------------------------------
def test_revoked_key_is_rejected(client):
    raw = auth.create_key("alice")
    assert auth.revoke_key("alice") == 1
    assert auth.verify_key(raw) is None
    assert client.get("/protected", headers={"X-API-Key": raw}).status_code == 401
