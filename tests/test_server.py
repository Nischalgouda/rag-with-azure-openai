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


def test_hashed_assets_are_cached_for_a_year_and_the_page_is_revalidated():
    assert server.cache_policy("/assets/index-C02giNA7.js") == "public, max-age=31536000, immutable"
    assert server.cache_policy("/assets/geist-latin-wght-normal-BgDaEnEv.woff2") == "public, max-age=31536000, immutable"
    assert server.cache_policy("/") == "no-cache"
    assert server.cache_policy("/index.html") == "no-cache"


def test_api_responses_are_never_cached():
    assert server.cache_policy("/api/ask") == "no-store"
    r = TestClient(server.app).get("/api/health")
    assert r.headers["Cache-Control"] == "no-store"


def test_large_text_responses_are_gzip_compressed(monkeypatch):
    monkeypatch.setattr(settings, "demo_mode", False)  # the OpenAPI schema is large enough to be compressed
    r = TestClient(server.app).get("/api/openapi.json", headers={"Accept-Encoding": "gzip"})
    assert r.status_code == 200
    assert r.headers["Content-Encoding"] == "gzip"
    assert r.json()["info"]["title"]  # and it still decodes to valid JSON

