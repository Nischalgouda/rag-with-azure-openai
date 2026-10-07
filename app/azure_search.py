"""Azure AI Search backend: replaces vectorstore.py + keyword.py + our RRF code.

One index holds the text, the vector, and the source. A single query can run keyword
(BM25) + vector (HNSW) search and fuse them with RRF server-side = hybrid search.
Optionally the semantic ranker re-ranks the top results with a language model."""
import time

import numpy as np
from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import ResourceNotFoundError
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SearchableField,
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    SemanticSearch,
    SimpleField,
    VectorSearch,
    VectorSearchProfile,
)
from azure.search.documents.models import VectorizedQuery

from app.config import settings
from app.embeddings import embed
from app.trace import ranked

SEMANTIC_CONFIG = "default-semantic"
VECTOR_PROFILE = "vec-profile"
EMBEDDING_DIMS = 1536  # text-embedding-3-small


def _credential() -> AzureKeyCredential:
    return AzureKeyCredential(settings.search_api_key)


def build_index() -> SearchIndex:
    fields = [
        SimpleField(name="id", type=SearchFieldDataType.String, key=True),
        SimpleField(name="source", type=SearchFieldDataType.String, filterable=True),
        SearchableField(name="text", type=SearchFieldDataType.String),
        SearchField(
            name="embedding",
            type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
            searchable=True,
            hidden=False,  # vector fields are not retrievable by default; we read them back for the cosine guardrail
            vector_search_dimensions=EMBEDDING_DIMS,
            vector_search_profile_name=VECTOR_PROFILE,
        ),
    ]
    vector_search = VectorSearch(
        algorithms=[HnswAlgorithmConfiguration(name="hnsw")],
        profiles=[VectorSearchProfile(name=VECTOR_PROFILE, algorithm_configuration_name="hnsw")],
    )
    semantic = SemanticSearch(configurations=[SemanticConfiguration(
        name=SEMANTIC_CONFIG,
        prioritized_fields=SemanticPrioritizedFields(content_fields=[SemanticField(field_name="text")]),
    )])
    return SearchIndex(name=settings.search_index_name, fields=fields,
                       vector_search=vector_search, semantic_search=semantic)


def _index_client() -> SearchIndexClient:
    return SearchIndexClient(settings.search_endpoint, _credential())


def _search_client() -> SearchClient:
    return SearchClient(settings.search_endpoint, settings.search_index_name, _credential())


def upload(vectors: np.ndarray, records: list[dict]) -> None:
    """Drop and recreate the index, then upload all chunks."""
    idx = _index_client()
    try:
        idx.delete_index(settings.search_index_name)
    except ResourceNotFoundError:
        pass
    idx.create_index(build_index())
    docs = [{"id": str(i), "source": r["source"], "text": r["text"],
             "embedding": vectors[i].tolist()} for i, r in enumerate(records)]
    _search_client().upload_documents(documents=docs)
    time.sleep(2)  # indexing is eventually consistent; let documents become searchable


def _query(q: np.ndarray, question: str, mode: str, top: int, semantic: bool = False) -> list[dict]:
    """One Azure AI Search query. Cosine is recomputed locally from the returned vectors because
    hybrid scores from the service are rank-fusion scores (~0.03), not similarities - useless for a
    'refuse if weak' guardrail. `stage_score` is the service's own ranking score."""
    kwargs: dict = {"select": ["id", "source", "text", "embedding"], "top": top}
    if mode in ("vector", "hybrid"):
        kwargs["vector_queries"] = [VectorizedQuery(
            vector=q.tolist(), k_nearest_neighbors=50, fields="embedding")]
    if mode in ("keyword", "hybrid"):
        kwargs["search_text"] = question
    if semantic:
        kwargs.update(query_type="semantic", semantic_configuration_name=SEMANTIC_CONFIG)

    out: list[dict] = []
    for r in _search_client().search(**kwargs):
        cosine = float(np.dot(q, np.array(r["embedding"], dtype=np.float32)))
        out.append({
            "chunk_id": int(r["id"]), "source": r["source"], "text": r["text"],
            "cosine": cosine, "stage_score": float(r.get("@search.score") or 0.0),
        })
    return out


def search(question: str, mode: str, k: int, want_trace: bool = False):
    """Returns (hits, top_cosine, stages) like rag.retrieve_full.

    The guardrail's top_cosine comes only from the main query, so asking for a trace can never
    change whether a question is answered. The per-stage rankings need two extra queries
    (vector-only and keyword-only), which is why a trace is opt-in."""
    q = embed([question])[0]
    main = _query(q, question, mode, k, semantic=settings.use_semantic_ranker and mode == "hybrid")

    hits = [(c["cosine"], {"chunk_id": c["chunk_id"], "source": c["source"], "text": c["text"]}) for c in main]
    top = max((c["cosine"] for c in main), default=0.0)

    stages = None
    if want_trace:
        vector = main if mode == "vector" else _query(q, question, "vector", 50)
        keyword = main if mode == "keyword" else _query(q, question, "keyword", 50)
        stages = {
            "vector": ranked([{**c, "stage_score": c["cosine"]} for c in vector]),
            "keyword": ranked(keyword),
            "fused": ranked(main),
        }
    return hits, top, stages
