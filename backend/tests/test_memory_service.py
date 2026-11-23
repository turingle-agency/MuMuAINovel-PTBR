import hashlib

import numpy as np
import pytest
from qdrant_client import QdrantClient

from app.services.vector import set_embedder_for_tests, set_vector_store_for_tests
from app.services.vector.qdrant_store import QdrantVectorStore


class FakeEmbedder:
    """Vetores determinísticos de 384 dimensões a partir de hash (sem modelo)."""

    def _one(self, text: str) -> np.ndarray:
        seed = int.from_bytes(hashlib.sha256(text.encode()).digest()[:4], "big")
        return np.random.default_rng(seed).standard_normal(384).astype(np.float32)

    def encode(self, texts):
        if isinstance(texts, str):
            return self._one(texts)
        return np.stack([self._one(t) for t in texts])


@pytest.fixture
def fake_env():
    set_vector_store_for_tests(QdrantVectorStore(QdrantClient(":memory:")))
    set_embedder_for_tests(FakeEmbedder())
    yield
    set_vector_store_for_tests(None)
    set_embedder_for_tests(None)


async def test_memory_service_roundtrip(fake_env):
    from app.services.memory_service import memory_service

    ok = await memory_service.add_memory("u", "p", "m1", "O herói perdeu a espada", "plot_point", {"chapter_number": 3})
    assert ok
    res = await memory_service.search_memories("u", "p", "O herói perdeu a espada", limit=5)
    assert res[0]["id"] == "m1"
    assert res[0]["content"] == "O herói perdeu a espada"
    assert res[0]["metadata"]["chapter_number"] == 3
    assert 0.0 <= res[0]["similarity"] <= 1.0
    assert res[0]["distance"] == pytest.approx(1 - res[0]["similarity"])


async def test_search_projeto_vazio(fake_env):
    from app.services.memory_service import memory_service

    assert await memory_service.search_memories("u", "vazio", "x", limit=5) == []


async def test_filtros_de_busca(fake_env):
    from app.services.memory_service import memory_service

    await memory_service.batch_add_memories("u", "p", [
        {"id": "a", "content": "um", "type": "plot_point", "metadata": {"chapter_number": 1, "importance_score": 0.9}},
        {"id": "b", "content": "dois", "type": "hook", "metadata": {"chapter_number": 5, "importance_score": 0.2}},
    ])
    res = await memory_service.search_memories("u", "p", "um", memory_types=["hook"], limit=5)
    assert [r["id"] for r in res] == ["b"]
    res = await memory_service.search_memories("u", "p", "um", min_importance=0.5, chapter_range=(1, 3), limit=5)
    assert [r["id"] for r in res] == ["a"]


async def test_recentes_e_foreshadows(fake_env):
    from app.services.memory_service import memory_service

    await memory_service.batch_add_memories("u", "p", [
        {"id": "a", "content": "um", "type": "plot_point", "metadata": {"chapter_number": 2, "importance_score": 0.9, "is_foreshadow": 1}},
        {"id": "b", "content": "dois", "type": "plot_point", "metadata": {"chapter_number": 4, "importance_score": 0.8}},
    ])
    rec = await memory_service.get_recent_memories("u", "p", current_chapter=4, recent_count=3)
    assert [r["id"] for r in rec] == ["a"]
    fs = await memory_service.find_unresolved_foreshadows("u", "p", current_chapter=4)
    assert [f["id"] for f in fs] == ["a"]


async def test_delete_chapter_memories(fake_env):
    from app.services.memory_service import memory_service

    await memory_service.add_memory("u", "p", "m1", "x", "plot_point", {"chapter_id": "ch1", "chapter_number": 1})
    await memory_service.add_memory("u", "p", "m2", "y", "plot_point", {"chapter_id": "ch2", "chapter_number": 2})
    assert await memory_service.delete_chapter_memories("u", "p", "ch1")
    stats = await memory_service.get_memory_stats("u", "p")
    assert stats["total_count"] == 1


async def test_delete_foreshadow_e_projeto_e_update(fake_env):
    from app.services.memory_service import memory_service

    await memory_service.add_memory("u", "p", "f1", "A chave dourada", "foreshadow", {"chapter_number": 1})
    await memory_service.add_memory("u", "p", "m1", "outra coisa", "plot_point", {"chapter_number": 1})
    assert await memory_service.update_memory("u", "p", "m1", content="texto novo", metadata={"importance": 0.1})
    res = await memory_service.search_memories("u", "p", "texto novo", limit=1)
    assert res[0]["id"] == "m1" and res[0]["metadata"]["importance"] == 0.1
    assert res[0]["metadata"]["memory_type"] == "plot_point"
    assert await memory_service.delete_foreshadow_memories("u", "p", ["dourada"]) == 1
    assert (await memory_service.get_memory_stats("u", "p"))["total_count"] == 1
    assert await memory_service.delete_project_memories("u", "p")
    assert (await memory_service.get_memory_stats("u", "p"))["total_count"] == 0
    assert await memory_service.delete_project_memories("u", "p")


def test_knowledge_search_base_vazia(fake_env):
    from app.services.knowledge_vector_store import knowledge_vector_store

    assert knowledge_vector_store.search("u", "kb1", "x", top_k=5) == []


def test_knowledge_upsert_search_delete(fake_env):
    from app.services.knowledge_vector_store import knowledge_vector_store

    items = [
        {"id": f"c{i}", "content": f"trecho {i}", "project_id": "p", "knowledge_base_id": "kb1",
         "document_id": f"d{i % 2}", "chunk_index": i, "title": "T", "heading_path": ["A"]}
        for i in range(3)
    ]
    knowledge_vector_store.upsert("u", items)
    hits = knowledge_vector_store.search("u", "kb1", "trecho 1", top_k=50)
    assert hits[0]["chunk_id"] == "c1"
    assert 0.0 <= hits[0]["score"] <= 1.0
    assert len(hits) == 3
    only = knowledge_vector_store.search("u", "kb1", "trecho 1", top_k=5, document_ids=["d0"])
    assert {h["chunk_id"] for h in only} == {"c0", "c2"}
    knowledge_vector_store.delete_document("u", "d0")
    assert [h["chunk_id"] for h in knowledge_vector_store.search("u", "kb1", "x", top_k=5)] == ["c1"]
    assert knowledge_vector_store.search("u", "outra_kb", "x", top_k=5) == []
