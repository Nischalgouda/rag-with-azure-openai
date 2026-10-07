# syntax=docker/dockerfile:1

# ---- Stage 1: build the frontend ------------------------------------------------------------
FROM node:22-alpine AS web
WORKDIR /web
COPY frontend/package.json frontend/package-lock.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# ---- Stage 2: slim runtime serving the API and the built UI ---------------------------------
FROM python:3.11-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1
WORKDIR /code

# Dependencies first, so this layer is cached until requirements change.
COPY requirements-prod.txt .
RUN pip install -r requirements-prod.txt

COPY app ./app
COPY scripts ./scripts
COPY data ./data
COPY --from=web /web/dist ./static

# Run as an unprivileged user; only /code/var is writable.
RUN useradd --create-home --uid 10001 appuser && mkdir -p /code/var && chown appuser /code/var
USER appuser

# Secrets (keys) are NOT baked in: they are injected as environment variables at deploy time.
ENV DEMO_MODE=true \
    STATIC_DIR=/code/static \
    DB_PATH=/code/var/usage.db \
    INDEX_DIR=/code/var/index \
    VECTOR_STORE=azure_search \
    EMBEDDING_PROVIDER=azure \
    LLM_PROVIDER=azure \
    MIN_SCORE=0.23

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s --start-period=10s \
  CMD python -c "import urllib.request, sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/health').status == 200 else 1)"

# --proxy-headers: trust the platform ingress's X-Forwarded-For so per-IP limits see the real visitor.
CMD ["uvicorn", "app.server:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips=*"]
