"""BM25 keyword scoring. Vector search finds meaning; keyword search finds exact terms
(product names, error codes, acronyms like 'RRF') that embeddings often blur. Azure AI
Search runs both and fuses them - that's 'hybrid search'."""
import math
import re
from collections import Counter

import numpy as np


def tokenize(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower())


def bm25_scores(query: str, docs: list[str], k1: float = 1.5, b: float = 0.75) -> np.ndarray:
    tokenized = [tokenize(d) for d in docs]
    n = len(docs)
    if n == 0:
        return np.zeros(0)
    avg_len = sum(len(t) for t in tokenized) / n or 1.0
    df = Counter(term for toks in tokenized for term in set(toks))
    scores = np.zeros(n)
    for term in set(tokenize(query)):
        if term not in df:
            continue
        idf = math.log(1 + (n - df[term] + 0.5) / (df[term] + 0.5))
        for i, toks in enumerate(tokenized):
            tf = toks.count(term)
            if tf:
                scores[i] += idf * tf * (k1 + 1) / (tf + k1 * (1 - b + b * len(toks) / avg_len))
    return scores
