import pytest
from qdrant_client import QdrantClient

from app.services.vector.base import Cond, VectorPoint
from app.services.vector.qdrant_store import QdrantVectorStore

DIM = 384


def vec(i: int) -> list[float]:
    v = [0.0] * DIM
    v[i] = 1.0
    return v


@pytest.fixture
def store():
    return QdrantVectorStore(QdrantClient(":memory:"))


def test_query_colecao_vazia(store):
    store.ensure_collection("c")
    assert store.query("c", [0.1] * DIM, limit=50) == []


def test_query_colecao_inexistente(store):
    assert store.query("nao_existe", [0.1] * DIM, limit=5) == []


def test_id_nao_uuid_volta_original(store):
    store.upsert("c", [VectorPoint(id="foreshadow:ch1:abc", document="x", payload={"chapter_number": 1}, vector=[0.1] * DIM)])
    hits = store.query("c", [0.1] * DIM, limit=10)
    assert hits[0].id == "foreshadow:ch1:abc"
    assert hits[0].document == "x"
    assert hits[0].payload == {"chapter_number": 1}
    assert hits[0].score == pytest.approx(1.0, abs=1e-4)


def test_upsert_mesmo_id_substitui(store):
    store.upsert("c", [VectorPoint(id="a", document="v1", payload={}, vector=vec(0))])
    store.upsert("c", [VectorPoint(id="a", document="v2", payload={}, vector=vec(0))])
    assert store.count("c") == 1
    assert store.get("c")[0].document == "v2"


def test_limit_maior_que_total(store):
    store.upsert("c", [VectorPoint(id="a", document="a", payload={}, vector=vec(0))])
    assert len(store.query("c", vec(0), limit=100)) == 1


def _seed(store):
    store.upsert("c", [
        VectorPoint(id="p1", document="d1", payload={"chapter_number": 1, "memory_type": "a"}, vector=vec(0)),
        VectorPoint(id="p5", document="d5", payload={"chapter_number": 5, "memory_type": "b"}, vector=vec(1)),
        VectorPoint(id="p9", document="d9", payload={"chapter_number": 9, "memory_type": "a"}, vector=vec(2)),
    ])


def test_filtros(store):
    _seed(store)
    got = store.get("c", where=[Cond("memory_type", "eq", "a"), Cond("chapter_number", "gte", 2)])
    assert [p.payload["chapter_number"] for p in got] == [9]
    got = store.get("c", where=[Cond("memory_type", "in", ["a", "b"]), Cond("chapter_number", "lte", 5)])
    assert sorted(p.id for p in got) == ["p1", "p5"]
    assert store.count("c", where=[Cond("memory_type", "eq", "a")]) == 2


def test_query_com_filtro(store):
    _seed(store)
    hits = store.query("c", vec(0), limit=5, where=[Cond("memory_type", "eq", "b")])
    assert [h.id for h in hits] == ["p5"]


def test_delete_por_ids_e_filtro(store):
    _seed(store)
    store.delete("c", ids=["p1"])
    assert store.count("c") == 2
    store.delete("c", where=[Cond("memory_type", "eq", "b")])
    assert [p.id for p in store.get("c")] == ["p9"]
    store.delete("c")  # sem ids nem filtro: não apaga nada
    assert store.count("c") == 1


def test_delete_collection_e_inexistente(store):
    _seed(store)
    store.delete_collection("c")
    assert store.count("c") == 0
    store.delete_collection("c")  # idempotente


def test_set_payload(store):
    _seed(store)
    store.set_payload("c", "p1", {"memory_type": "z"})
    got = store.get("c", where=[Cond("memory_type", "eq", "z")])
    assert [p.id for p in got] == ["p1"]
    assert got[0].document == "d1"
