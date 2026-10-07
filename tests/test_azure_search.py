"""The Azure AI Search adapter, tested against a fake search client (no network, no Azure)."""
import pytest

from app import azure_search
from app.config import settings
from tests.conftest import fake_embed

DOCS = [
    ("0", "azure_ai_search.md", "Hybrid search merges keyword and vector results using Reciprocal Rank Fusion", 0.033),
    ("1", "rag_concepts.md", "Chunk overlap prevents facts from being cut in half at a boundary", 0.016),
    ("2", "docker_azure_deploy.md", "Copy requirements before source code so Docker caches the install layer", 0.008),
]


class FakeSearchClient:
    def __init__(self) -> None:
        self.calls: list[dict] = []

    def search(self, **kwargs):
        self.calls.append(kwargs)
        return iter(
            {"id": i, "source": src, "text": text, "embedding": fake_embed([text])[0].tolist(),
             "@search.score": score}
            for i, src, text, score in DOCS
        )


@pytest.fixture()
def client(monkeypatch):
    fake = FakeSearchClient()
    monkeypatch.setattr(azure_search, "_search_client", lambda: fake)
    return fake


QUESTION = "How does hybrid search merge keyword and vector results?"


def test_without_a_trace_exactly_one_query_is_made(client):
    hits, top, stages = azure_search.search(QUESTION, "hybrid", 3, want_trace=False)
    assert len(client.calls) == 1
    assert stages is None
    assert len(hits) == 3
    assert top == max(cos for cos, _ in hits)
    assert hits[0][1]["chunk_id"] == 0


def test_hybrid_query_sends_both_text_and_vector(client):
    azure_search.search(QUESTION, "hybrid", 3)
    call = client.calls[0]
    assert call["search_text"] == QUESTION
    assert call["vector_queries"]


def test_a_trace_costs_two_extra_queries_vector_only_and_keyword_only(client):
    _, _, stages = azure_search.search(QUESTION, "hybrid", 3, want_trace=True)
    assert len(client.calls) == 3
    # the queries run concurrently, so identify them by content rather than by order
    hybrid = [c for c in client.calls if "vector_queries" in c and "search_text" in c]
    vector_only = [c for c in client.calls if "vector_queries" in c and "search_text" not in c]
    keyword_only = [c for c in client.calls if "search_text" in c and "vector_queries" not in c]
    assert (len(hybrid), len(vector_only), len(keyword_only)) == (1, 1, 1)
    assert set(stages) == {"vector", "keyword", "fused"}


def test_vector_mode_reuses_the_main_query_for_the_vector_stage(client):
    azure_search.search(QUESTION, "vector", 3, want_trace=True)
    assert len(client.calls) == 2  # main (= vector) + keyword-only


def test_requesting_a_trace_does_not_change_the_guardrail_score(client):
    _, plain_top, _ = azure_search.search(QUESTION, "hybrid", 3, want_trace=False)
    _, traced_top, _ = azure_search.search(QUESTION, "hybrid", 3, want_trace=True)
    assert plain_top == traced_top


def test_vector_stage_reports_cosine_as_its_score(client):
    _, _, stages = azure_search.search(QUESTION, "hybrid", 3, want_trace=True)
    for chunk in stages["vector"]:
        assert chunk["stage_score"] == pytest.approx(chunk["cosine"], abs=1e-3)


def test_semantic_ranker_is_only_used_for_hybrid_when_enabled(client, monkeypatch):
    monkeypatch.setattr(settings, "use_semantic_ranker", True)
    azure_search.search(QUESTION, "hybrid", 3)
    assert client.calls[-1]["query_type"] == "semantic"
    azure_search.search(QUESTION, "vector", 3)
    assert "query_type" not in client.calls[-1]
