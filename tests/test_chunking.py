import pytest

from app.chunking import chunk_text
from app.vectorstore import VectorStore
import numpy as np


def test_chunks_respect_size_and_cover_text():
    text = "Sentence number one. " * 200
    chunks = chunk_text(text, size=300, overlap=50)
    assert len(chunks) > 1
    assert all(len(c) <= 300 for c in chunks)
    assert chunks[0].startswith("Sentence number one.")


def test_overlap_shares_text_between_neighbours():
    text = " ".join(f"word{i}" for i in range(400))
    chunks = chunk_text(text, size=200, overlap=60)
    tail = chunks[0][-20:]
    assert tail.split()[-1] in chunks[1]


def test_invalid_overlap_raises():
    with pytest.raises(ValueError):
        chunk_text("abc", size=10, overlap=10)


def test_vector_search_returns_nearest(tmp_path):
    store = VectorStore(str(tmp_path))
    vecs = np.array([[1, 0], [0, 1]], dtype=np.float32)
    store.add(vecs, [{"source": "a", "text": "x"}, {"source": "b", "text": "y"}])
    hits = store.search(np.array([0.9, 0.1], dtype=np.float32), k=1)
    assert hits[0][1]["source"] == "a"
