"""Production entrypoint: one process serving the API under /api and the built frontend at /.

    uvicorn app.server:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips="*"

Same-origin serving means no CORS configuration is needed. `--proxy-headers` makes uvicorn trust
X-Forwarded-For from the platform's ingress, so per-IP rate limits see the visitor's real address
(only safe because the container is reachable solely through that ingress).

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
