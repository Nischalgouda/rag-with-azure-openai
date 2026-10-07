"""The whole RAG loop: ingest() and answer(), with retrieval in the middle."""
from pathlib import Path

import numpy as np

from app import azure_search, llm
from app.chunking import chunk_text
from app.config import settings
from app.embeddings import embed
from app.keyword import bm25_scores
from app.trace import build_trace, ranked
from app.vectorstore import VectorStore

store = VectorStore(settings.index_dir)

SYSTEM_PROMPT = (
    "You answer questions using ONLY the context provided. "
    "If the context does not contain the answer, say you don't know. "
    "Cite sources as [source] after the facts you use."
)

RRF_K = 60  # standard Reciprocal Rank Fusion constant


def ingest(folder: str) -> int:
    """Read .txt/.md files -> chunk -> embed -> store. Returns number of chunks."""
    records: list[dict] = []
    for path in sorted(Path(folder).glob("**/*")):
        if path.suffix.lower() in {".txt", ".md"}:
            for chunk in chunk_text(path.read_text(encoding="utf-8"),
                                    settings.chunk_size, settings.chunk_overlap):
                records.append({"source": path.name, "text": chunk})
    if not records:
        return 0
    vectors = embed([r["text"] for r in records])
    if settings.vector_store == "azure_search":
        azure_search.upload(vectors, records)
    else:
        store.clear()
        store.add(vectors, records)
    return len(records)


def _retrieve_local(question: str, mode: str, k: int, want_trace: bool):
    if not store.records:
        return [], 0.0, None

    cos = store.vectors @ embed([question])[0]
    vec_order = [int(i) for i in np.argsort(cos)[::-1]]

    kw = bm25_scores(question, [r["text"] for r in store.records])
    kw_order = [int(i) for i in np.argsort(kw)[::-1] if kw[i] > 0]

    fused: dict[int, float] = {}
    for ranking in (vec_order, kw_order):
        for rank, idx in enumerate(ranking):
            fused[idx] = fused.get(idx, 0.0) + 1 / (RRF_K + rank + 1)
    fused_order = sorted(fused, key=fused.get, reverse=True)

    if mode == "vector":
        order, score_of = vec_order, lambda i: float(cos[i])
    elif mode == "keyword":
        order, score_of = kw_order, lambda i: float(kw[i])
    else:  # hybrid: Reciprocal Rank Fusion rewards chunks ranked high by EITHER method
        order, score_of = fused_order, lambda i: fused[i]

    def item(i: int, stage_score: float) -> dict:
        rec = store.records[i]
        return {"chunk_id": i, "source": rec["source"], "text": rec["text"],
                "cosine": float(cos[i]), "stage_score": stage_score}

    top_ids = order[:k]
    hits = [(float(cos[i]), {**store.records[i], "chunk_id": i}) for i in top_ids]
    stages = None
    if want_trace:
        stages = {
            "vector": ranked([item(i, float(cos[i])) for i in vec_order]),
            "keyword": ranked([item(i, float(kw[i])) for i in kw_order]),
            "fused": ranked([item(i, score_of(i)) for i in top_ids]),
        }
    return hits, float(cos.max()), stages


def retrieve_full(question: str, mode: str | None = None, k: int | None = None, want_trace: bool = False):
    """Returns (hits, top_cosine, stages). hits = [(cosine, record)] in final ranked order.

    top_cosine is the best semantic similarity among the retrieved candidates; it drives the
    'refuse to answer' guardrail. It never depends on `want_trace`, so tracing cannot change
    whether a question is answered."""
    mode = mode or settings.search_mode
    k = k or settings.top_k
    if settings.vector_store == "azure_search":
        return azure_search.search(question, mode, k, want_trace)
    return _retrieve_local(question, mode, k, want_trace)


def retrieve(question: str, mode: str | None = None, k: int | None = None):
    """(hits, top_cosine) - the form used by the evaluation harness."""
    hits, top, _ = retrieve_full(question, mode, k)
    return hits, top


def answer(question: str, mode: str | None = None, trace: bool = False) -> dict:
    """Retrieve -> (guardrail) -> augment prompt -> generate."""
    mode = mode or settings.search_mode
    hits, top_score, stages = retrieve_full(question, mode, want_trace=trace)

    # Guardrail: weak retrieval means we'd be asking the LLM to guess. Refuse instead.
    refused = not hits or top_score < settings.min_score
    if refused:
        result = {"answer": "I don't know - nothing relevant in the indexed documents.",
                  "sources": [], "top_score": top_score, "tokens": 0}
    else:
        context = "\n\n".join(f"[{rec['source']}]\n{rec['text']}" for _, rec in hits)
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
        ]
        text, tokens = llm.chat(messages)
        sources = [{"source": rec["source"], "score": round(s, 3), "text": rec["text"][:200]}
                   for s, rec in hits]
        result = {"answer": text, "sources": sources, "top_score": top_score, "tokens": tokens}

    if trace:
        result["trace"] = build_trace(mode, settings.min_score, top_score, refused, stages)
    return result
