"""Banco vetorial atrás de interface própria (implementação: Qdrant)."""
from __future__ import annotations

from app.services.vector.base import Cond, VectorHit, VectorPoint, VectorStore
from app.services.vector.embedder import Embedder, get_embedder, set_embedder_for_tests

_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    global _store
    if _store is None:
        from qdrant_client import QdrantClient

        from app.config import settings
        from app.services.vector.qdrant_store import QdrantVectorStore

        if settings.qdrant_url:
            client = QdrantClient(url=settings.qdrant_url, api_key=settings.qdrant_api_key)
        else:
            client = QdrantClient(path=settings.qdrant_path)
        _store = QdrantVectorStore(client)
    return _store


def set_vector_store_for_tests(store: VectorStore | None) -> None:
    global _store
    _store = store


__all__ = [
    "Cond", "VectorPoint", "VectorHit", "VectorStore", "Embedder",
    "get_vector_store", "get_embedder", "set_vector_store_for_tests", "set_embedder_for_tests",
]
