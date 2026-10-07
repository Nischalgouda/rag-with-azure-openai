"""Shared fixtures. Every test runs hermetically: no Azure, no model download, no network.

* `fake_embed` maps words to hashed dimensions, so texts sharing words have a high cosine and
  unrelated texts a near-zero one - enough to exercise retrieval, the guardrail and tracing.
* The chat model is replaced by a stub returning a fixed answer and 42 tokens.
* Settings, the SQLite file and the local index live in a per-test temp directory.
"""
import hashlib
import re

import numpy as np
import pytest

from app import azure_search, llm, rag
from app.config import settings

DIMS = 512
STOP = {"does", "with", "from", "that", "this", "what", "have", "your", "into", "than"}


def fake_embed(texts: list[str]) -> np.ndarray:
    out = np.zeros((len(texts), DIMS), dtype=np.float32)
    for row, text in enumerate(texts):
        for token in re.findall(r"[a-z0-9]+", text.lower()):
            if len(token) < 4 or token in STOP:
                continue
            out[row, int(hashlib.md5(token.encode()).hexdigest(), 16) % DIMS] += 1
    norms = np.linalg.norm(out, axis=1, keepdims=True)
    return out / np.clip(norms, 1e-12, None)


@pytest.fixture(autouse=True)
def hermetic(tmp_path, monkeypatch):
    monkeypatch.setattr(rag, "embed", fake_embed)
    monkeypatch.setattr(azure_search, "embed", fake_embed)
    monkeypatch.setattr(settings, "vector_store", "local")
    monkeypatch.setattr(settings, "db_path", str(tmp_path / "test.db"))
    monkeypatch.setattr(settings, "min_score", 0.15)
    monkeypatch.setattr(settings, "demo_mode", False)
    monkeypatch.setattr(settings, "demo_enabled", True)
    monkeypatch.setattr(rag.store, "dir", tmp_path / "index")
    monkeypatch.setattr(rag.store, "vectors", np.zeros((0, 0), dtype=np.float32))
    monkeypatch.setattr(rag.store, "records", [])
    monkeypatch.setattr(llm, "chat", lambda messages: ("FAKE ANSWER [azure_ai_search.md]", 42))


@pytest.fixture()
def indexed():
    """The sample documents, ingested into the (temporary) local index."""
    assert rag.ingest("data") > 0
