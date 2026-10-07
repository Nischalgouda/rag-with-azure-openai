"""Public-demo protections: auth tiers, rate limits, daily caps, the cost budget and the kill switch."""
import pytest
from fastapi.testclient import TestClient

from app import auth, limits, llm, main
from app.config import settings
from app.ratelimit import RateLimiter
from tests.helpers import FakeClock

Q = {"question": "How big is the free tier of Azure AI Search?"}


@pytest.fixture()
def demo(indexed, monkeypatch):
    """Demo mode on, with generous per-second limits so each test can tighten exactly one rule."""
    monkeypatch.setattr(settings, "demo_mode", True)
    monkeypatch.setattr(limits, "anon_limiter", RateLimiter(100, 0.01, clock=FakeClock()))
    monkeypatch.setattr(limits, "keyed_limiter", RateLimiter(100, 0.01, clock=FakeClock()))
    return TestClient(main.app)


# ---- admin-only endpoints ----------------------------------------------------------------
def test_ingest_requires_a_key_in_demo_mode(demo):
    assert demo.post("/ingest", json={"folder": "data"}).status_code == 401


def test_ingest_rejects_a_valid_non_admin_key(demo):
    key = auth.create_key("alice")
    r = demo.post("/ingest", json={"folder": "data"}, headers={"X-API-Key": key})
    assert r.status_code == 403


def test_ingest_and_usage_work_for_an_admin_key(demo):
    key = auth.create_key("admin")
    assert demo.post("/ingest", json={"folder": "data"}, headers={"X-API-Key": key}).status_code == 200
    assert demo.get("/usage", headers={"X-API-Key": key}).status_code == 200


def test_usage_is_not_public_in_demo_mode(demo):
    assert demo.get("/usage").status_code == 401


# ---- anonymous and keyed access ------------------------------------------------------------
def test_anonymous_visitors_can_ask(demo):
    assert demo.post("/ask", json=Q).status_code == 200


def test_a_wrong_key_is_rejected_not_treated_as_anonymous(demo):
    assert demo.post("/ask", json=Q, headers={"X-API-Key": "rk_wrong"}).status_code == 401


def test_a_valid_key_is_accepted(demo):
    key = auth.create_key("alice")
    assert demo.post("/ask", json=Q, headers={"X-API-Key": key}).status_code == 200


# ---- rate limit (burst) ---------------------------------------------------------------------
def test_burst_limit_returns_429_with_retry_after(demo, monkeypatch):
    monkeypatch.setattr(limits, "anon_limiter", RateLimiter(2, 30, clock=FakeClock()))
    assert demo.post("/ask", json=Q).status_code == 200
    assert demo.post("/ask", json=Q).status_code == 200
    r = demo.post("/ask", json=Q)
    assert r.status_code == 429
    assert int(r.headers["Retry-After"]) >= 1


# ---- daily caps and budget -------------------------------------------------------------------
def test_daily_question_cap_per_visitor(demo, monkeypatch):
    monkeypatch.setattr(settings, "anon_daily_questions", 2)
    assert demo.post("/ask", json=Q).status_code == 200
    assert demo.post("/ask", json=Q).status_code == 200
    r = demo.post("/ask", json=Q)
    assert r.status_code == 429
    assert "Daily limit of 2" in r.json()["detail"]
    assert int(r.headers["Retry-After"]) > 0


def test_a_key_holder_gets_a_larger_allowance_than_an_anonymous_visitor(demo, monkeypatch):
    monkeypatch.setattr(settings, "anon_daily_questions", 1)
    key = auth.create_key("alice")
    assert demo.post("/ask", json=Q).status_code == 200
    assert demo.post("/ask", json=Q).status_code == 429
    assert demo.post("/ask", json=Q, headers={"X-API-Key": key}).status_code == 200
    assert demo.post("/ask", json=Q, headers={"X-API-Key": key}).status_code == 200


def test_global_token_budget_stops_everyone(demo, monkeypatch):
    monkeypatch.setattr(settings, "daily_token_budget", 40)  # one answer costs 42 tokens
    key = auth.create_key("alice")
    assert demo.post("/ask", json=Q).status_code == 200
    r = demo.post("/ask", json=Q, headers={"X-API-Key": key})
    assert r.status_code == 429
    assert "budget" in r.json()["detail"].lower()


def test_remaining_questions_are_reported_in_a_header(demo, monkeypatch):
    monkeypatch.setattr(settings, "anon_daily_questions", 5)
    r = demo.post("/ask", json=Q)
    assert r.headers["X-Daily-Limit"] == "5"
    assert r.headers["X-Daily-Remaining"] == "4"
    assert demo.post("/ask", json=Q).headers["X-Daily-Remaining"] == "3"


# ---- kill switch and error hygiene ------------------------------------------------------------
def test_kill_switch_returns_503(demo, monkeypatch):
    monkeypatch.setattr(settings, "demo_enabled", False)
    assert demo.post("/ask", json=Q).status_code == 503


def test_public_502_does_not_leak_upstream_details(demo, monkeypatch):
    def fail(messages):
        raise ConnectionError("https://secret-endpoint.openai.azure.com refused the connection")

    monkeypatch.setattr(llm, "chat", fail)
    r = demo.post("/ask", json=Q)
    assert r.status_code == 502
    assert "secret-endpoint" not in r.text


def test_dev_mode_has_no_limits(indexed, monkeypatch):
    monkeypatch.setattr(settings, "anon_daily_questions", 1)
    client = TestClient(main.app)
    assert all(client.post("/ask", json=Q).status_code == 200 for _ in range(3))
