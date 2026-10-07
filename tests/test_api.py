"""API behaviour in normal (dev) mode. The chat model and embeddings are faked in conftest.py."""
import pytest
from fastapi.testclient import TestClient

from app import db, llm, main


@pytest.fixture()
def client(indexed):
    return TestClient(main.app)


def test_health_reports_the_store_and_chunk_count(client):
    body = client.get("/health").json()
    assert body["status"] == "ok"
    assert body["vector_store"] == "local"
    assert body["chunks_indexed"] > 0


def test_ask_answers_with_sources_and_logs_usage(client):
    r = client.post("/ask", json={"question": "How big is the free tier of Azure AI Search?"})
    body = r.json()
    assert r.status_code == 200
    assert body["answer"].startswith("FAKE ANSWER")
    assert body["sources"] and body["session_id"]
    assert db.usage_summary()["total_tokens"] == 42


def test_off_topic_question_is_refused_without_calling_the_llm(client, monkeypatch):
    def boom(messages):
        raise AssertionError("LLM must not be called for off-topic questions")

    monkeypatch.setattr(llm, "chat", boom)
    body = client.post("/ask", json={"question": "How do I bake a sourdough loaf?"}).json()
    assert "don't know" in body["answer"].lower()
    assert body["sources"] == []
    assert body["tokens"] == 0


def test_llm_failure_returns_502_with_detail_in_dev_mode(client, monkeypatch):
    def fail(messages):
        raise ConnectionError("endpoint down")

    monkeypatch.setattr(llm, "chat", fail)
    r = client.post("/ask", json={"question": "How big is the free tier of Azure AI Search?"})
    assert r.status_code == 502
    assert "endpoint down" in r.json()["detail"]


def test_empty_question_is_rejected(client):
    assert client.post("/ask", json={"question": ""}).status_code == 422


def test_ingest_and_usage_are_open_in_dev_mode(client):
    assert client.post("/ingest", json={"folder": "data"}).status_code == 200
    assert client.get("/usage").status_code == 200
