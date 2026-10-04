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


def search(question: str, mode: str, k: int) -> tuple[list[tuple[float, dict]], float]:
    """Returns (hits, top_cosine) like rag.retrieve. Cosine is recomputed locally from the
    returned vectors because hybrid scores from the service are rank-fusion scores
    (~0.03), not similarities - useless for a 'refuse if weak' guardrail."""
    q = embed([question])[0]
    kwargs: dict = {"select": ["source", "text", "embedding"], "top": k}
    if mode in ("vector", "hybrid"):
        kwargs["vector_queries"] = [VectorizedQuery(
            vector=q.tolist(), k_nearest_neighbors=50, fields="embedding")]
    if mode in ("keyword", "hybrid"):
        kwargs["search_text"] = question
    if settings.use_semantic_ranker and mode == "hybrid":
        kwargs.update(query_type="semantic", semantic_configuration_name=SEMANTIC_CONFIG)

    hits: list[tuple[float, dict]] = []
    top = 0.0
    for r in _search_client().search(**kwargs):
        cos = float(np.dot(q, np.array(r["embedding"], dtype=np.float32)))
        top = max(top, cos)
        hits.append((cos, {"source": r["source"], "text": r["text"]}))
    return hits, top
