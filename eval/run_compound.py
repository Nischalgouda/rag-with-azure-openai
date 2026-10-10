"""Behaviour check for compound and injected questions. Run from the project root:  python -m eval.run_compound

Unlike eval.run_eval this CALLS THE REAL MODEL (a few hundred tokens per case), because the thing under test is whether the
model obeys the prompt. Each case lists text the answer must contain and text it must not. The model is not deterministic,
so a failure here means "look at the answer", and the hermetic tests in tests/test_prompt.py pin the prompt structure."""
import json
import sys
from pathlib import Path

from app import rag

CASES = json.loads((Path(__file__).parent / "compound_cases.json").read_text(encoding="utf-8"))


def check(case: dict) -> tuple[bool, str, str]:
    answer = rag.answer(case["q"])["answer"]
    low = answer.lower()
    missing = [s for s in case["must_contain"] if s.lower() not in low]
    leaked = [s for s in case["must_not_contain"] if s.lower() in low]
    problems = [f"missing {m!r}" for m in missing] + [f"contains {s!r}" for s in leaked]
    return not problems, "; ".join(problems), answer


if __name__ == "__main__":
    failures = 0
    for case in CASES:
        ok, why, answer = check(case)
        failures += not ok
        print(f"{'PASS' if ok else 'FAIL'}  {case['name']}")
        if not ok:
            print(f"      {why}\n      answer: {answer[:300]!r}")
    print(f"\n{len(CASES) - failures}/{len(CASES)} passed")
    sys.exit(1 if failures else 0)
