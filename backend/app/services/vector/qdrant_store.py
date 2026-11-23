"""Implementação de VectorStore com Qdrant."""
from __future__ import annotations

import uuid
from typing import Any

from qdrant_client import QdrantClient, models

from app.services.vector.base import Cond, VectorHit, VectorPoint

ID_KEY = "_id"
DOC_KEY = "_document"
_SCROLL_BATCH = 256


def _point_id(external_id: str) -> str:
    return str(uuid.uuid5(uuid.NAMESPACE_URL, external_id))


def _condition(cond: Cond) -> models.FieldCondition:
    if cond.op == "eq":
        return models.FieldCondition(key=cond.field, match=models.MatchValue(value=cond.value))
    if cond.op == "in":
        return models.FieldCondition(key=cond.field, match=models.MatchAny(any=list(cond.value)))
    if cond.op == "gte":
        return models.FieldCondition(key=cond.field, range=models.Range(gte=cond.value))
    if cond.op == "lte":
        return models.FieldCondition(key=cond.field, range=models.Range(lte=cond.value))
    raise ValueError(f"Operador de filtro desconhecido: {cond.op}")


def _filter(where: list[Cond] | None) -> models.Filter | None:
    if not where:
        return None
    return models.Filter(must=[_condition(c) for c in where])


def _split(payload: dict[str, Any] | None) -> tuple[str, str, dict]:
    data = dict(payload or {})
    external_id = data.pop(ID_KEY, "")
    document = data.pop(DOC_KEY, "")
    return external_id, document, data


class QdrantVectorStore:
    def __init__(self, client: QdrantClient):
        self.client = client

    def _exists(self, name: str) -> bool:
        return self.client.collection_exists(name)

    def ensure_collection(self, name: str, dim: int = 384) -> None:
        if not self._exists(name):
            self.client.create_collection(
                collection_name=name,
                vectors_config=models.VectorParams(size=dim, distance=models.Distance.COSINE),
            )

    def upsert(self, name: str, points: list[VectorPoint]) -> None:
        if not points:
            return
        dim = len(points[0].vector) if points[0].vector else 384
        self.ensure_collection(name, dim)
        structs = []
        for p in points:
            if p.vector is None:
                raise ValueError("VectorPoint sem vetor no upsert")
            payload = dict(p.payload)
            payload[ID_KEY] = p.id
            payload[DOC_KEY] = p.document
            structs.append(models.PointStruct(id=_point_id(p.id), vector=list(p.vector), payload=payload))
        self.client.upsert(collection_name=name, points=structs)

    def query(
        self, name: str, vector: list[float], limit: int, where: list[Cond] | None = None
    ) -> list[VectorHit]:
        if limit <= 0 or not self._exists(name):
            return []
        response = self.client.query_points(
            collection_name=name,
            query=list(vector),
            query_filter=_filter(where),
            limit=limit,
            with_payload=True,
        )
        hits = []
        for pt in response.points:
            external_id, document, payload = _split(pt.payload)
            hits.append(VectorHit(id=external_id, document=document, payload=payload, score=float(pt.score)))
        return hits

    def get(self, name: str, where: list[Cond] | None = None) -> list[VectorPoint]:
        if not self._exists(name):
            return []
        flt = _filter(where)
        out: list[VectorPoint] = []
        offset = None
        while True:
            records, offset = self.client.scroll(
                collection_name=name,
                scroll_filter=flt,
                limit=_SCROLL_BATCH,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )
            for rec in records:
                external_id, document, payload = _split(rec.payload)
                out.append(VectorPoint(id=external_id, document=document, payload=payload))
            if offset is None:
                break
        return out

    def delete(
        self, name: str, ids: list[str] | None = None, where: list[Cond] | None = None
    ) -> None:
        if not self._exists(name) or (not ids and not where):
            return
        if ids:
            selector: Any = models.PointIdsList(points=[_point_id(i) for i in ids])
            self.client.delete(collection_name=name, points_selector=selector)
        if where:
            self.client.delete(
                collection_name=name, points_selector=models.FilterSelector(filter=_filter(where))
            )

    def delete_collection(self, name: str) -> None:
        if self._exists(name):
            self.client.delete_collection(name)

    def count(self, name: str, where: list[Cond] | None = None) -> int:
        if not self._exists(name):
            return 0
        return self.client.count(collection_name=name, count_filter=_filter(where), exact=True).count

    def set_payload(self, name: str, id: str, payload: dict) -> None:
        if not self._exists(name):
            return
        clean = {k: v for k, v in payload.items() if k not in (ID_KEY, DOC_KEY)}
        self.client.set_payload(collection_name=name, payload=clean, points=[_point_id(id)])
