"""The production entrypoint: API under /api, hardened headers, interactive docs not exposed."""
from fastapi.testclient import TestClient

from app import server


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
