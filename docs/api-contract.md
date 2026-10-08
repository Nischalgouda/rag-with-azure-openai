# API contract

The contract between the backend (`app/`) and the frontend (`frontend/`). The frontend validates every
response against the matching zod schema in `frontend/src/api/schema.ts`; if the backend drifts from this
document the UI shows an explicit "unexpected response" error instead of rendering undefined values.
Backend behaviour is pinned by `tests/test_trace.py`, `tests/test_demo_mode.py` and `tests/test_api.py`.

In production the API is served under `/api` (see `app/server.py`); in development Vite proxies `/api/*`
to the FastAPI server, which serves the same routes at the root.

## `POST /ask`

```
Content-Type: application/json
X-API-Key: rk_...        optional; anonymous visitors get a smaller allowance in demo mode

{
  "question": "string, 1..2000 chars",
  "session_id": "string, optional",
  "mode": "vector" | "keyword" | "hybrid",     optional, default = server setting (hybrid)
  "trace": true | false                        optional, default false
}
```

`trace: true` asks for the per-stage retrieval trace. It is opt-in because under Azure AI Search it costs two
extra queries (vector-only and keyword-only). Requesting a trace never changes whether a question is answered.

### Success `200`

```jsonc
{
  "answer": "string",              // may contain [file.md] citations
  "sources": [{ "source": "file.md", "score": 0.42, "text": "first 200 chars" }],   // [] when refused
  "top_score": 0.42,               // best cosine similarity among retrieved candidates (drives the guardrail)
  "tokens": 589,                   // 0 when refused
  "session_id": "uuid",
  "latency_ms": 4448,
  "trace": {                       // only when the request had trace: true
    "mode": "hybrid",
    "threshold": 0.23,             // refuse when top_score < threshold
    "decision": "answered" | "refused",
    "top_score": 0.42,
    "stages": {
      "vector":  [RankedChunk],    // candidates by cosine, best first
      "keyword": [RankedChunk],    // candidates by BM25, best first
      "fused":   [RankedChunk]     // the top-k placed in the prompt (when answered)
    }
  }
}
```

```jsonc
RankedChunk = {
  "chunk_id": 3, "source": "rag_concepts.md", "text_preview": "first ~180 chars",
  "cosine": 0.31,        // always present: cosine(question, chunk)
  "rank": 2,             // 1-based, consecutive within a stage
  "stage_score": 0.0161  // what the stage ranks by: cosine | BM25 | RRF
}
```

### Response headers (demo mode only)

| Header | Meaning |
|---|---|
| `X-Daily-Limit` | questions allowed today for this caller (anonymous per IP, or per API key) |
| `X-Daily-Remaining` | questions left today after this one |

### Errors

| Status | When | Notes |
|---|---|---|
| 401 | an `X-API-Key` was sent but is invalid | one message for "missing" and "wrong", reveals nothing |
| 422 | invalid body (empty question, unknown mode) | FastAPI default |
| 429 | burst limit, daily question cap, or the shared daily token budget | always sends `Retry-After: <seconds>` |
| 502 | the model call failed | generic text in demo mode (no upstream details leaked) |
| 503 | kill switch (`DEMO_ENABLED=false`) | |

## Other endpoints

| Endpoint | Dev mode | `DEMO_MODE=true` |
|---|---|---|
| `GET /health` | open | open (includes `demo_mode`, `demo_enabled`) |
| `POST /ingest` | open | admin key only (401 without a key, 403 for a non-admin key) |
| `GET /usage` | open | admin key only |

Admin keys are those whose owner name is listed in `ADMIN_KEY_NAMES` (default `admin`).
Create one with `python -m scripts.create_key admin`.

Keys are issued by request, not self-service: a visitor asks the owner (the UI links to LinkedIn), and the owner runs
`python -m scripts.create_key <name>` and sends the key. Every key gets the same limits (below). Keys live in the app's
SQLite file, which is on the container's own disk, so they are lost on a redeploy unless a persistent volume is added.

## Demo-mode limits (all configurable in `app/config.py` / environment)

| Rule | Default |
|---|---|
| Burst (token bucket), anonymous | 4 requests, one more every 15 s |
| Burst, API key | 10 requests, one more every 4 s |
| Daily questions, anonymous (per IP, UTC day) | 15 |
| Daily questions, per API key | 200 |
| Shared daily token budget (all callers) | 150,000 tokens |

Rate-limit state is in process memory. That is correct for a single replica; with several replicas each
would count separately, and a shared store such as Redis would be the next step.
