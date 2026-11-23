"""Coleta limitada de evidências públicas com a API Firecrawl v2."""
import asyncio
from collections.abc import Awaitable, Callable
from hashlib import sha256
from ipaddress import ip_address
from socket import SOCK_STREAM
from urllib.parse import urlsplit

import httpx

from app.schemas.radar import CollectorInput, EvidenceItem, SourceResult, SourceStatus, public_url
from app.services.radar_collectors.base import (
    CollectionContext, CollectionError, observed_date, provider_json, text_excerpt,
)

URL = "https://api.firecrawl.dev/v2"
SEARCH_LIMIT = 5
SCRAPE_LIMIT = 3


async def resolve_addresses(host: str) -> list[str]:
    infos = await asyncio.get_running_loop().getaddrinfo(host, None, type=SOCK_STREAM)
    return [info[4][0] for info in infos]


class FirecrawlCollector:
    def __init__(self, http: httpx.AsyncClient,
                 *, resolver: Callable[[str], Awaitable[list[str]]] = resolve_addresses):
        self.http = http
        self.resolver = resolver

    async def _public_destination(self, url: str, context: CollectionContext) -> bool:
        host = urlsplit(url).hostname
        try:
            async with asyncio.timeout(context.remaining()):
                addresses = await self.resolver(host)
            return bool(addresses) and all(ip_address(address).is_global for address in addresses)
        except (OSError, TimeoutError, ValueError):
            return False

    async def collect(self, input: CollectorInput, context: CollectionContext) -> SourceResult:
        items = []
        notes = ["Busca por país, até 5 resultados e 3 páginas públicas lidas."]
        country = "UK" if input.country == "GB" else input.country
        status: SourceStatus = "not_configured"
        if context.credential:
            headers = {"Authorization": f"Bearer {context.credential}"}
            try:
                payload = await provider_json(self.http, context, "POST", f"{URL}/search", headers=headers, json={
                    "query": input.query, "country": country, "limit": SEARCH_LIMIT,
                    "sources": [{"type": "web"}],
                    "tbs": f"cdr:1,cd_min:{input.start_date:%m/%d/%Y},cd_max:{input.end_date:%m/%d/%Y}",
                })
                data = payload.get("data")
                rows = data.get("web") if isinstance(data, dict) else None
                if not isinstance(rows, list):
                    raise CollectionError("A busca retornou um formato inesperado.")
                status = await self._read_pages(rows, items, notes, input, context, headers)
            except CollectionError as error:
                status = "error"
                notes.append(str(error))
        else:
            notes.append("Cadastre a chave do Firecrawl para coletar.")

        return SourceResult(
            source="firecrawl", status=status, collected_at=context.clock(), scope=input.country,
            method_version="firecrawl-v2-1", items=items,
            limits={"sample_limit": SEARCH_LIMIT, "exhausted": status == "empty", "notes": notes},
        )

    async def _read_pages(self, rows, items, notes, input, context, headers):
        if not rows:
            return "empty"
        seen = set()
        scrape_count = 0
        partial = False
        for row in rows[:SEARCH_LIMIT]:
            if not isinstance(row, dict):
                partial = True
                continue
            original = row.get("url")
            url = public_url(original) if isinstance(original, str) else None
            if not url or url in seen:
                continue
            if not await self._public_destination(url, context):
                partial = True
                continue
            seen.add(url)
            label = text_excerpt(row.get("title"), context.credential) or "Resultado da web"
            excerpt = text_excerpt(row.get("description"), context.credential)
            date = observed_date(row.get("publishedDate") or row.get("date"))
            if scrape_count < SCRAPE_LIMIT:
                scrape_count += 1
                try:
                    data = await self._scrape(url, input, context, headers)
                    metadata = data.get("metadata")
                    if not isinstance(metadata, dict):
                        metadata = {}
                    redirect_url = metadata.get("sourceURL")
                    if redirect_url and (
                        not isinstance(redirect_url, str) or not public_url(redirect_url)
                        or not await self._public_destination(redirect_url, context)
                    ):
                        raise CollectionError("Leitura descartada por destino indisponível.")
                    excerpt = text_excerpt(data.get("markdown"), context.credential) or excerpt
                    date = date or observed_date(metadata.get("publishedTime"))
                except CollectionError as error:
                    partial = True
                    notes.append(str(error))

            items.append(EvidenceItem(
                id=sha256(url.encode()).hexdigest(), url=url, label=label, kind="content",
                observed_date=date, data={"excerpt": excerpt or None},
            ))
        if not items:
            notes.append("A busca retornou resultados sem páginas públicas elegíveis.")
            return "error"
        return "partial" if partial else "ok"

    async def _scrape(self, url, input, context, headers):
        payload = await provider_json(self.http, context, "POST", f"{URL}/scrape", headers=headers, json={
            "url": url, "formats": ["markdown"], "onlyMainContent": True,
            "location": {"country": input.country, "languages": [input.language]},
        })
        data = payload.get("data")
        if not isinstance(data, dict) or not isinstance(data.get("markdown"), str):
            raise CollectionError("A leitura retornou um formato inesperado.")
        return data
