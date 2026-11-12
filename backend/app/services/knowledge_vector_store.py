"""Adaptador de armazenamento vetorial da base de conhecimento (VectorStore + embedder)."""
from __future__ import annotations

import hashlib
import json
from typing import Any

from app.services.vector import Cond, VectorPoint, get_embedder, get_vector_store


class KnowledgeVectorStore:
    @property
    def store(self):
        return get_vector_store()

    @property
    def embedder(self):
        return get_embedder()

    def _collection_name(self, user_id: str) -> str:
        user_hash = hashlib.sha256(user_id.encode()).hexdigest()[:12]
        return f"knowledge_u_{user_hash}"

    def upsert(self, user_id: str, items: list[dict[str, Any]]) -> None:
        if not items:
            return
        name = self._collection_name(user_id)
        contents = [item["content"] for item in items]
        embeddings = self.embedder.encode(contents).tolist()
        points = []
        for item, embedding in zip(items, embeddings):
            payload = {
                "user_id": user_id,
                "project_id": item["project_id"],
                "knowledge_base_id": item["knowledge_base_id"],
                "document_id": item["document_id"],
                "chunk_index": int(item["chunk_index"]),
                "title": item.get("title", "")[:200],
                "original_filename": item.get("original_filename", "")[:500],
                "section_title": item.get("section_title") or "",
                "heading_path": json.dumps(item.get("heading_path") or [], ensure_ascii=False),
            }
            points.append(VectorPoint(id=item["id"], document=item["content"], payload=payload, vector=embedding))
        self.store.upsert(name, points)

    def delete_document(self, user_id: str, document_id: str) -> None:
        self.store.delete(self._collection_name(user_id), where=[Cond("document_id", "eq", document_id)])

    def search(
        self,
        user_id: str,
        knowledge_base_id: str,
        query: str,
        top_k: int,
        document_ids: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        name = self._collection_name(user_id)
        where = [Cond("knowledge_base_id", "eq", knowledge_base_id)]
        if document_ids:
            where.append(Cond("document_id", "in", list(document_ids)))
        # Base nova/vazia: não carrega o modelo nem consulta.
        if self.store.count(name, where) == 0:
            return []
        query_embedding = self.embedder.encode(query).tolist()
        hits: list[dict[str, Any]] = []
        for hit in self.store.query(name, query_embedding, top_k, where):
            distance = 1.0 - hit.score
            score = max(0.0, min(1.0, 1.0 - distance / 2.0))
            hits.append({
                "chunk_id": hit.id,
                "content": hit.document,
                "score": score,
                "distance": distance,
                "metadata": hit.payload,
            })
        return hits


knowledge_vector_store = KnowledgeVectorStore()
