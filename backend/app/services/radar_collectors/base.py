"""Contrato interno de coleta do Radar."""
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Protocol

from app.schemas.radar import CollectorInput, SourceResult

Clock = Callable[[], datetime]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True)
class CollectionContext:
    admin_id: str
    research_id: str
    deadline: datetime
    clock: Clock = utc_now
    credential: str | None = field(default=None, repr=False)

    def remaining(self) -> float:
        return max(0.0, (self.deadline - self.clock()).total_seconds())


class Collector(Protocol):
    async def collect(self, input: CollectorInput, context: CollectionContext) -> SourceResult:
        ...
