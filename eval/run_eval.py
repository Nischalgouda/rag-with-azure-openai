"""Retrieval evaluation. Run from project root:  python -m eval.run_eval

Measures, per search mode:
  hit@k      - did a retrieved chunk contain the expected fact? (answerable questions)
  refusal    - did the guardrail correctly refuse unanswerable questions?
No LLM is called, so it is free, fast and deterministic - evaluate retrieval separately
from generation, because if retrieval is wrong no prompt can save you."""
import json
from pathlib import Path

from app import rag
from app.config import settings

QUESTIONS = json.loads((Path(__file__).parent / "questions.json").read_text(encoding="utf-8"))


def evaluate(mode: str, k: int) -> dict:
    hit = answerable = refused = unanswerable = 0
    misses = []
    for item in QUESTIONS:
        hits, top = rag.retrieve(item["q"], mode=mode, k=k)
        if item["expect"] is None:
            unanswerable += 1
            if top < settings.min_score:
                refused += 1
            else:
                misses.append(f"should refuse (score {top:.2f}): {item['q']}")
        else:
            answerable += 1
            if any(item["expect"].lower() in rec["text"].lower() for _, rec in hits):
                hit += 1
            else:
                misses.append(f"missed '{item['expect']}': {item['q']}")
    return {"hit": f"{hit}/{answerable}", "refusal": f"{refused}/{unanswerable}", "misses": misses}


if __name__ == "__main__":
    n = rag.ingest("data")
    print(f"Indexed {n} chunks (size={settings.chunk_size}, overlap={settings.chunk_overlap})\n")
    for k in (1, 3):
        for mode in ("vector", "keyword", "hybrid"):
            r = evaluate(mode, k)
            print(f"k={k} {mode:8s} hit@k={r['hit']:6s} refusal={r['refusal']}")
            for m in r["misses"]:
                print("     -", m)
