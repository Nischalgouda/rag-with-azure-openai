"""The retrieval trace returned when the client sends `trace: true` (see docs/api-contract.md)."""
import pytest
from fastapi.testclient import TestClient

from app import main
from app.config import settings

ANSWERABLE = {"question": "How does hybrid search merge keyword and vector results?"}
OFF_TOPIC = {"question": "How do I bake a sourdough loaf?"}


@pytest.fixture()
def client(indexed):
    return TestClient(main.app)


def ask(client, body, **extra):
    r = client.post("/ask", json={**body, **extra})
    assert r.status_code == 200, r.text
    return r.json()


def test_no_trace_unless_requested(client):
    assert "trace" not in ask(client, ANSWERABLE)
    assert "trace" not in ask(client, ANSWERABLE, trace=False)


def test_trace_has_the_contract_shape(client):
    trace = ask(client, ANSWERABLE, trace=True)["trace"]
    assert set(trace) == {"mode", "threshold", "decision", "top_score", "stages"}
    assert trace["mode"] == "hybrid"
    assert trace["threshold"] == settings.min_score
    assert set(trace["stages"]) == {"vector", "keyword", "fused"}
    chunk = trace["stages"]["vector"][0]
    assert set(chunk) == {"chunk_id", "source", "text_preview", "cosine", "rank", "stage_score"}


def test_answered_trace_matches_the_sources_sent_to_the_model(client):
    body = ask(client, ANSWERABLE, trace=True)
    assert body["trace"]["decision"] == "answered"
    fused_sources = [c["source"] for c in body["trace"]["stages"]["fused"]]
    assert fused_sources == [s["source"] for s in body["sources"]]


def test_refused_trace_matches_an_empty_source_list(client):
    body = ask(client, OFF_TOPIC, trace=True)
    assert body["trace"]["decision"] == "refused"
    assert body["sources"] == []
    assert body["trace"]["top_score"] < body["trace"]["threshold"]


def test_ranks_are_one_based_and_consecutive_within_each_stage(client):
    stages = ask(client, ANSWERABLE, trace=True)["trace"]["stages"]
    for chunks in stages.values():
        assert [c["rank"] for c in chunks] == list(range(1, len(chunks) + 1))


def test_vector_stage_lists_every_chunk_best_first(client):
    stages = ask(client, ANSWERABLE, trace=True)["trace"]["stages"]
    cosines = [c["cosine"] for c in stages["vector"]]
    assert cosines == sorted(cosines, reverse=True)
    assert len(stages["vector"]) == client.get("/health").json()["chunks_indexed"]


def test_keyword_mode_orders_the_prompt_by_bm25(client):
    trace = ask(client, ANSWERABLE, trace=True, mode="keyword")["trace"]
    assert trace["mode"] == "keyword"
    fused_ids = [c["chunk_id"] for c in trace["stages"]["fused"]]
    keyword_ids = [c["chunk_id"] for c in trace["stages"]["keyword"]]
    assert fused_ids == keyword_ids[: len(fused_ids)]


def test_requesting_a_trace_never_changes_the_outcome(client):
    plain = ask(client, ANSWERABLE)
    traced = ask(client, ANSWERABLE, trace=True)
    assert plain["answer"] == traced["answer"]
    assert plain["top_score"] == traced["top_score"]
    assert [s["source"] for s in plain["sources"]] == [s["source"] for s in traced["sources"]]


def test_an_unknown_mode_is_rejected(client):
    assert client.post("/ask", json={**ANSWERABLE, "mode": "magic"}).status_code == 422
