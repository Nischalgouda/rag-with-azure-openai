import logging
import time
import uuid

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from app import db, rag
from app.config import settings

logging.basicConfig(level=logging.INFO)
logging.getLogger("azure").setLevel(logging.WARNING)  # the Azure SDK logs every HTTP request at INFO
log = logging.getLogger("rag")

app = FastAPI(title="Azure-ready RAG demo")


class AskRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    session_id: str | None = None


class IngestRequest(BaseModel):
    folder: str = "data"


@app.get("/health")
def health():
    if settings.vector_store == "azure_search":
        return {"status": "ok", "vector_store": "azure_search", "index": settings.search_index_name}
    return {"status": "ok", "vector_store": "local", "chunks_indexed": len(rag.store.records)}


@app.post("/ingest")
def ingest(req: IngestRequest):
    n = rag.ingest(req.folder)
    if n == 0:
        raise HTTPException(404, f"No .txt/.md files found in '{req.folder}'")
    return {"chunks_indexed": n}


@app.post("/ask")
def ask(req: AskRequest):
    session_id = req.session_id or str(uuid.uuid4())
    start = time.perf_counter()
    try:
        result = rag.answer(req.question)
    except Exception as exc:  # e.g. LLM endpoint unreachable
        log.exception("ask failed")
        raise HTTPException(502, f"Model call failed: {exc}") from exc
    latency_ms = int((time.perf_counter() - start) * 1000)
    db.log_query(session_id, req.question, result["answer"],
                 result["top_score"], result["tokens"], latency_ms)
    log.info("session=%s score=%.2f tokens=%s %dms", session_id,
             result["top_score"], result["tokens"], latency_ms)
    return {**result, "session_id": session_id, "latency_ms": latency_ms}


@app.get("/usage")
def usage():
    return db.usage_summary()
