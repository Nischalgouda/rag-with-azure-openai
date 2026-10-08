"""Production entrypoint: one process serving the API under /api and the built frontend at /.

    uvicorn app.server:app --host 0.0.0.0 --port 8000

Same-origin serving means no CORS configuration is needed. Per-visitor rate limits need the real client
address: behind the platform ingress set TRUSTED_PROXY_HOPS=1 and app.limits.client_ip uses the LAST
X-Forwarded-For entry (the one our own proxy appended). Earlier entries are client-supplied and can be
forged, so uvicorn's --proxy-headers (which trusts them) is deliberately not used.

For local development keep using `uvicorn app.main:app` plus the Vite dev server.
"""
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.main import app as api

app = FastAPI(title="RAG X-ray", docs_url=None, redoc_url=None, openapi_url=None)

SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "strict-origin-when-cross-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    "Content-Security-Policy": (
        "default-src 'self'; img-src 'self' data:; style-src 'self'; script-src 'self'; "
        "connect-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'"
    ),
}


# The mounted API app has its own interactive docs and OpenAPI schema (under /api). The public demo does not
# need to advertise its endpoint map, so they are hidden in demo mode (404) and stay available locally.
HIDDEN_IN_DEMO = {"/api/docs", "/api/redoc", "/api/openapi.json", "/api/docs/oauth2-redirect"}


@app.middleware("http")
async def hide_schema_in_demo(request: Request, call_next):
    if settings.demo_mode and request.url.path.rstrip("/") in HIDDEN_IN_DEMO:
        return PlainTextResponse("Not Found", status_code=404)
    return await call_next(request)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    for name, value in SECURITY_HEADERS.items():
        response.headers.setdefault(name, value)
    return response


app.mount("/api", api)

_static = Path(settings.static_dir)
if _static.is_dir():
    # Mounted last: it is a catch-all, so /api/* must be registered first.
    app.mount("/", StaticFiles(directory=_static, html=True), name="frontend")
