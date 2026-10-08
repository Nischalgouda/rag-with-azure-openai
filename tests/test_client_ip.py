"""Visitor identification behind a reverse proxy: the limits must not be bypassable by forging headers."""
import pytest
from fastapi.testclient import TestClient

from app import limits, main
from app.config import settings
from app.ratelimit import RateLimiter
from tests.helpers import FakeClock

Q = {"question": "How do I bake a sourdough loaf?"}  # refused: costs no model tokens


class FakeRequest:
    def __init__(self, forwarded: str | None, host: str = "10.0.0.5") -> None:
        self.headers = {"x-forwarded-for": forwarded} if forwarded is not None else {}
        self.client = type("C", (), {"host": host})()


def test_the_header_is_ignored_when_no_proxy_is_trusted(monkeypatch):
    monkeypatch.setattr(settings, "trusted_proxy_hops", 0)
    assert limits.client_ip(FakeRequest("1.2.3.4")) == "10.0.0.5"


def test_one_trusted_proxy_means_the_last_entry_is_the_visitor(monkeypatch):
    monkeypatch.setattr(settings, "trusted_proxy_hops", 1)
    assert limits.client_ip(FakeRequest("203.0.113.7")) == "203.0.113.7"


def test_entries_forged_by_the_client_to_the_left_are_ignored(monkeypatch):
    monkeypatch.setattr(settings, "trusted_proxy_hops", 1)
    # the client sent "6.6.6.6, 7.7.7.7"; our proxy appended the address it actually saw
    assert limits.client_ip(FakeRequest("6.6.6.6, 7.7.7.7, 203.0.113.7")) == "203.0.113.7"


def test_two_trusted_proxies_pick_the_second_from_the_right(monkeypatch):
    monkeypatch.setattr(settings, "trusted_proxy_hops", 2)
    assert limits.client_ip(FakeRequest("9.9.9.9, 203.0.113.7, 10.1.1.1")) == "203.0.113.7"


def test_missing_or_short_header_falls_back_to_the_socket_address(monkeypatch):
    monkeypatch.setattr(settings, "trusted_proxy_hops", 2)
    assert limits.client_ip(FakeRequest(None)) == "10.0.0.5"
    assert limits.client_ip(FakeRequest("203.0.113.7")) == "10.0.0.5"  # fewer entries than trusted hops


@pytest.fixture()
def demo(indexed, monkeypatch):
    monkeypatch.setattr(settings, "demo_mode", True)
    monkeypatch.setattr(settings, "trusted_proxy_hops", 1)
    monkeypatch.setattr(limits, "anon_limiter", RateLimiter(2, 600, clock=FakeClock()))
    return TestClient(main.app)


def test_rotating_a_fake_leftmost_address_does_not_dodge_the_burst_limit(demo):
    real = "203.0.113.7"
    statuses = [demo.post("/ask", json=Q, headers={"X-Forwarded-For": f"10.0.0.{i}, {real}"}).status_code
                for i in range(1, 5)]
    assert statuses == [200, 200, 429, 429]


def test_different_real_visitors_have_separate_limits(demo):
    for ip in ("203.0.113.7", "203.0.113.8"):
        assert demo.post("/ask", json=Q, headers={"X-Forwarded-For": ip}).status_code == 200
