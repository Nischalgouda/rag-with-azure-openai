"""API tests with the chat model faked, so they run offline. Embeddings are real (local)."""
import pytest
from fastapi.testclient import TestClient

from app import db, llm, main, rag
from app.config import settings


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "db_path", str(tmp_path / "usage.db"))
    monkeypatch.setattr(rag.store, "dir", tmp_path / "index")
    monkeypatch.setattr(llm, "chat", lambda messages: ("FAKE ANSWER [azure_ai_search.md]", 42))
    rag.ingest("data")
    return TestClient(main.app)


def test_health_reports_indexed_chunks(client):
    assert client.get("/health").json()["chunks_indexed"] > 0


def test_ask_answers_with_sources_and_logs_usage(client):
    r = client.post("/ask", json={"question": "How big is the free tier of Azure AI Search?"})
    body = r.json()
    assert r.status_code == 200
    assert body["answer"].startswith("FAKE ANSWER")
    assert body["sources"] and body["session_id"]
    assert db.usage_summary()["total_tokens"] == 42


def test_off_topic_question_is_refused_without_calling_llm(client, monkeypatch):
    def boom(messages):
        raise AssertionError("LLM must not be called for off-topic questions")
    monkeypatch.setattr(llm, "chat", boom)
    body = client.post("/ask", json={"question": "How do I bake a sourdough loaf?"}).json()
    assert "don't know" in body["answer"].lower()
    assert body["sources"] == []


def test_llm_failure_returns_502(client, monkeypatch):
    def fail(messages):
        raise ConnectionError("endpoint down")
    monkeypatch.setattr(llm, "chat", fail)
    r = client.post("/ask", json={"question": "What does the semantic ranker do?"})
    assert r.status_code == 502


def test_empty_question_rejected(client):
    assert client.post("/ask", json={"question": ""}).status_code == 422
