import logging
import time
import uuid
from typing import Literal

from fastapi import Depends, FastAPI, HTTPException, Response
from pydantic import BaseModel, Field

from app import db, limits, rag
from app.config import settings

logging.basicConfig(level=logging.INFO)
logging.getLogger("azure").setLevel(logging.WARNING)  # the Azure SDK logs every HTTP request at INFO
log = logging.getLogger("rag")

app = FastAPI(title="RAG with Azure OpenAI")


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    session_id: str | None = None
    mode: Literal["vector", "keyword", "hybrid"] | None = None  # default: settings.search_mode
    trace: bool = False  # opt in to the per-stage retrieval trace (see docs/api-contract.md)


class IngestRequest(BaseModel):
    folder: str = "data"


@app.get("/health")
def health():
    info = {"status": "ok", "demo_mode": settings.demo_mode, "demo_enabled": settings.demo_enabled}
    if settings.vector_store == "azure_search":
        return {**info, "vector_store": "azure_search", "index": settings.search_index_name}
    return {**info, "vector_store": "local", "chunks_indexed": len(rag.store.records)}


@app.post("/ingest", dependencies=[Depends(limits.require_admin)])
def ingest(req: IngestRequest):
    n = rag.ingest(req.folder)
    if n == 0:
        raise HTTPException(404, f"No .txt/.md files found in '{req.folder}'")
    return {"chunks_indexed": n}


@app.post("/ask")
def ask(req: AskRequest, response: Response, caller: limits.Caller = Depends(limits.guard_ask)):
    session_id = req.session_id or str(uuid.uuid4())
    start = time.perf_counter()
    try:
        result = rag.answer(req.question, mode=req.mode, trace=req.trace)
    except Exception as exc:  # e.g. LLM endpoint unreachable
        log.exception("ask failed")
        # Upstream error text can contain endpoints and request ids: keep it out of public responses.
        detail = "The model service is unavailable. Please try again shortly." if settings.demo_mode \
            else f"Model call failed: {exc}"
        raise HTTPException(502, detail) from exc
    latency_ms = int((time.perf_counter() - start) * 1000)
    db.log_query(session_id, req.question, result["answer"],
                 result["top_score"], result["tokens"], latency_ms, caller.identity)
    log.info("session=%s who=%s score=%.2f tokens=%s %dms", session_id, caller.identity,
             result["top_score"], result["tokens"], latency_ms)
    if settings.demo_mode:
        response.headers["X-Daily-Remaining"] = str(caller.remaining_after_this)
        response.headers["X-Daily-Limit"] = str(caller.daily_cap)
    return {**result, "session_id": session_id, "latency_ms": latency_ms}


@app.get("/usage", dependencies=[Depends(limits.require_admin)])
def usage():
    return db.usage_summary()
