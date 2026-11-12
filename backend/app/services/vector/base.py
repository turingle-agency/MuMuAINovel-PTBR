"""Tipos e interface do banco vetorial (independente de implementação)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Protocol


@dataclass(frozen=True)
class Cond:
    field: str
    op: Literal["eq", "in", "gte", "lte"]
    value: Any


@dataclass
class VectorPoint:
    id: str
    document: str
    payload: dict
    vector: list[float] | None = None


@dataclass
class VectorHit:
    id: str
    document: str
    payload: dict
    score: float  # similaridade cosseno


class VectorStore(Protocol):
    def ensure_collection(self, name: str, dim: int = 384) -> None: ...

    def upsert(self, name: str, points: list[VectorPoint]) -> None: ...

    def query(
        self, name: str, vector: list[float], limit: int, where: list[Cond] | None = None
    ) -> list[VectorHit]: ...

    def get(self, name: str, where: list[Cond] | None = None) -> list[VectorPoint]: ...

    def delete(
        self, name: str, ids: list[str] | None = None, where: list[Cond] | None = None
    ) -> None: ...

    def delete_collection(self, name: str) -> None: ...

    def count(self, name: str, where: list[Cond] | None = None) -> int: ...

    def set_payload(self, name: str, id: str, payload: dict) -> None: ...
