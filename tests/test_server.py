"""The production entrypoint: API under /api, hardened headers, interactive docs not exposed."""
from fastapi.testclient import TestClient

from app import server
from app.config import settings


def test_api_is_mounted_under_api_prefix():
    r = TestClient(server.app).get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_security_headers_are_set():
    r = TestClient(server.app).get("/api/health")
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    csp = r.headers["Content-Security-Policy"]
    assert "default-src 'self'" in csp and "frame-ancestors 'none'" in csp


def test_the_content_security_policy_forbids_inline_scripts():
    csp = TestClient(server.app).get("/api/health").headers["Content-Security-Policy"]
    assert "'unsafe-inline'" not in csp


def test_interactive_docs_are_not_exposed_at_the_root():
    assert TestClient(server.app).get("/docs").status_code == 404


def test_the_api_schema_and_docs_are_hidden_in_demo_mode(monkeypatch):
    monkeypatch.setattr(settings, "demo_mode", True)
    client = TestClient(server.app)
    for path in ("/api/openapi.json", "/api/docs", "/api/redoc", "/api/docs/"):
        assert client.get(path).status_code == 404, path
    assert client.get("/api/health").status_code == 200  # the real API is unaffected


def test_the_api_schema_stays_available_outside_demo_mode(monkeypatch):
    monkeypatch.setattr(settings, "demo_mode", False)
    assert TestClient(server.app).get("/api/openapi.json").status_code == 200
