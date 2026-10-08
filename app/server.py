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
