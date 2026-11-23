"""Contrato interno de coleta do Radar."""
import asyncio
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
import re
from typing import Protocol

import httpx

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


class CollectionError(ValueError):
    """Falha com mensagem controlada para a fotografia."""


async def provider_json(client: httpx.AsyncClient, context: CollectionContext, method: str,
                        url: str, **kwargs) -> dict:
    try:
        remaining = context.remaining()
        if not remaining:
            raise TimeoutError
        async with asyncio.timeout(remaining):
            response = await client.request(method, url, follow_redirects=False, **kwargs)
        try:
            payload = response.json()
        except ValueError:
            payload = None
        error = payload.get("error") if isinstance(payload, dict) else None
        errors = error.get("errors", []) if isinstance(error, dict) else []
        if not isinstance(errors, list):
            errors = []
        reasons = {
            item.get("reason") for item in errors if isinstance(item, dict)
            and isinstance(item.get("reason"), str)
        }
        if "commentsDisabled" in reasons:
            raise CollectionError("Comentários desativados neste vídeo.")
        if response.status_code in (402, 429) or reasons & {"quotaExceeded", "rateLimitExceeded"}:
            raise CollectionError("Limite de uso da fonte atingido.")
        if response.status_code in (401, 403):
            raise CollectionError("A fonte recusou a credencial ou o acesso.")
        if not response.is_success or not isinstance(payload, dict) or payload.get("success") is False:
            raise CollectionError("A fonte retornou uma resposta indisponível.")
        return payload
    except (TimeoutError, httpx.TimeoutException):
        raise CollectionError("Tempo de coleta esgotado.") from None
    except httpx.HTTPError:
        raise CollectionError("Não foi possível acessar a fonte.") from None


def text_excerpt(value, credential: str | None = None) -> str:
    if not isinstance(value, str):
        return ""
    if credential:
        value = value.replace(credential, "")
    value = re.sub(r"<[^>]*>|https?://[^\s<>]+", "", value)
    return " ".join(value.split())[:500]


def observed_date(value) -> date | None:
    try:
        return date.fromisoformat(value[:10]) if isinstance(value, str) else None
    except ValueError:
        return None
