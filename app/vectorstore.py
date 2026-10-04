"""A deliberately tiny vector store: a numpy matrix + a list of chunk records.

Searching = one matrix multiply (cosine similarity against every chunk), then sort.
This is exactly what Azure AI Search does at scale (with ANN indexes so it doesn't
have to compare against everything). Build it by hand once and the managed service
stops being magic."""
import json
from pathlib import Path

import numpy as np


class VectorStore:
    def __init__(self, index_dir: str):
        self.dir = Path(index_dir)
        self.vectors = np.zeros((0, 0), dtype=np.float32)
        self.records: list[dict] = []  # {"source": str, "text": str}
        self._load()

    def add(self, vectors: np.ndarray, records: list[dict]) -> None:
        self.vectors = vectors if len(self.records) == 0 else np.vstack([self.vectors, vectors])
        self.records.extend(records)
        self._save()

    def search(self, query_vec: np.ndarray, k: int) -> list[tuple[float, dict]]:
        if not self.records:
            return []
        scores = self.vectors @ query_vec  # cosine similarity (vectors are normalized)
        top = np.argsort(scores)[::-1][:k]
        return [(float(scores[i]), self.records[i]) for i in top]

    def clear(self) -> None:
        self.vectors = np.zeros((0, 0), dtype=np.float32)
        self.records = []
        self._save()

    def _save(self) -> None:
        self.dir.mkdir(exist_ok=True)
        np.save(self.dir / "vectors.npy", self.vectors)
        (self.dir / "records.json").write_text(json.dumps(self.records), encoding="utf-8")

    def _load(self) -> None:
        v, r = self.dir / "vectors.npy", self.dir / "records.json"
        if v.exists() and r.exists():
            self.vectors = np.load(v)
            self.records = json.loads(r.read_text(encoding="utf-8"))
