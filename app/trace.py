"""Builds the retrieval trace returned by POST /ask when the client sends `trace: true`.
The shape is the contract in docs/api-contract.md and mirrors frontend/src/api/schema.ts."""


def _preview(text: str, limit: int = 180) -> str:
    return text[:limit] + ("…" if len(text) > limit else "")


def ranked(items: list[dict]) -> list[dict]:
    """items: [{chunk_id, source, text, cosine, stage_score}] already sorted best-first."""
    return [
        {
            "chunk_id": int(it["chunk_id"]),
            "source": it["source"],
            "text_preview": _preview(it["text"]),
            "cosine": round(float(it["cosine"]), 4),
            "rank": i + 1,
            "stage_score": round(float(it["stage_score"]), 4),
        }
        for i, it in enumerate(items)
    ]


def build_trace(mode: str, threshold: float, top_score: float, refused: bool,
                stages: dict[str, list[dict]] | None) -> dict:
    stages = stages or {"vector": [], "keyword": [], "fused": []}
    return {
        "mode": mode,
        "threshold": threshold,
        "decision": "refused" if refused else "answered",
        "top_score": top_score,
        "stages": stages,
    }
