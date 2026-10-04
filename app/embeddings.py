"""Turn text into vectors. An embedding is a list of numbers where texts with similar
MEANING land close together. This is the upgrade over your hashmap: lookup by meaning,
not by exact key."""
import numpy as np

from app.config import settings

_local_model = None


def _normalize(vectors: np.ndarray) -> np.ndarray:
    # Unit-length vectors make cosine similarity a plain dot product.
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    return vectors / np.clip(norms, 1e-12, None)


def embed(texts: list[str]) -> np.ndarray:
    if settings.embedding_provider == "azure":
        from app.llm import get_client  # same SDK client as chat

        client = get_client()
        resp = client.embeddings.create(
            model=settings.azure_openai_embedding_deployment,  # Azure: deployment name
            input=texts,
        )
        vectors = np.array([d.embedding for d in resp.data], dtype=np.float32)
    else:
        global _local_model
        if _local_model is None:
            from fastembed import TextEmbedding

            _local_model = TextEmbedding(settings.local_embedding_model)
        vectors = np.array(list(_local_model.embed(texts)), dtype=np.float32)
    return _normalize(vectors)
