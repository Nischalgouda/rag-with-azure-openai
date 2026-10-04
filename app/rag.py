"""The whole RAG loop: ingest() and answer(), with retrieve() in the middle."""
from pathlib import Path

import numpy as np

from app import azure_search, llm
from app.chunking import chunk_text
from app.config import settings
from app.embeddings import embed
from app.keyword import bm25_scores
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


def retrieve(question: str, mode: str | None = None, k: int | None = None):
    """Returns (hits, top_cosine). hits = [(cosine, record)] in final ranked order.

    top_cosine is the best semantic similarity over the whole index; it drives the
    'refuse to answer' guardrail regardless of which mode ordered the results."""
    mode = mode or settings.search_mode
    k = k or settings.top_k
    if settings.vector_store == "azure_search":
        return azure_search.search(question, mode, k)
    if not store.records:
        return [], 0.0

    cos = store.vectors @ embed([question])[0]
    vec_order = list(np.argsort(cos)[::-1])

    kw = bm25_scores(question, [r["text"] for r in store.records])
    kw_order = [int(i) for i in np.argsort(kw)[::-1] if kw[i] > 0]

    if mode == "vector":
        order = vec_order
    elif mode == "keyword":
        order = kw_order
    else:  # hybrid: Reciprocal Rank Fusion - rewards chunks ranked high by EITHER method
        fused: dict[int, float] = {}
        for ranking in (vec_order, kw_order):
            for rank, idx in enumerate(ranking):
                fused[int(idx)] = fused.get(int(idx), 0.0) + 1 / (RRF_K + rank + 1)
        order = sorted(fused, key=fused.get, reverse=True)

    hits = [(float(cos[i]), store.records[i]) for i in order[:k]]
    return hits, float(cos.max())


def answer(question: str) -> dict:
    """Retrieve -> (guardrail) -> augment prompt -> generate."""
    hits, top_score = retrieve(question)

    # Guardrail: weak retrieval means we'd be asking the LLM to guess. Refuse instead.
    if not hits or top_score < settings.min_score:
        return {"answer": "I don't know - nothing relevant in the indexed documents.",
                "sources": [], "top_score": top_score, "tokens": 0}

    context = "\n\n".join(f"[{rec['source']}]\n{rec['text']}" for _, rec in hits)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {question}"},
    ]
    text, tokens = llm.chat(messages)
    sources = [{"source": rec["source"], "score": round(s, 3), "text": rec["text"][:200]}
               for s, rec in hits]
    return {"answer": text, "sources": sources, "top_score": top_score, "tokens": tokens}
