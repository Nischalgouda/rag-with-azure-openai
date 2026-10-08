"""Capture REAL responses for the example questions so the UI can replay them instantly.

    python -m scripts.capture_saved_runs

Runs each example question (frontend/src/data/examples.json, the same list the UI chips use) through the live
stack in hybrid mode with a trace, and writes frontend/src/data/saved-runs.json. Why: clicking an example then
costs nothing, never hits a daily limit, and still works if the shared token budget is used up. The UI labels
these as saved runs and offers "Run it live". Re-run this whenever the documents, model or threshold change.
"""
import datetime
import json
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import settings

settings.demo_mode = False  # capture without demo limits
from app.main import app  # noqa: E402  (import after the setting so the guards see it)

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / "frontend" / "src" / "data" / "examples.json"
OUT = ROOT / "frontend" / "src" / "data" / "saved-runs.json"


def main() -> None:
    questions = [e["question"] for e in json.loads(EXAMPLES.read_text(encoding="utf-8"))]
    client = TestClient(app)
    runs: dict[str, dict] = {}
    for q in questions:
        r = client.post("/ask", json={"question": q, "mode": "hybrid", "trace": True})
        r.raise_for_status()
        body = r.json()
        body["session_id"] = "saved"
        runs[q] = body
        print(f"captured: {q!r} -> {body['trace']['decision']}, top {body['top_score']:.2f}, {body['tokens']} tokens")

    out = {
        "generated_at": datetime.date.today().isoformat(),
        "mode": "hybrid",
        "chat_deployment": settings.azure_openai_chat_deployment,
        "runs": runs,
    }
    OUT.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
