import json
from datetime import datetime, timedelta, timezone

import httpx
import pytest

from app.schemas.radar import CollectorInput
from app.services.radar_collectors.base import CollectionContext
from app.services.radar_collectors.firecrawl import FirecrawlCollector

NOW = datetime(2026, 11, 23, 12, tzinfo=timezone.utc)
INPUT = CollectorInput(query="Marcações para crochê", country="BR", language="pt-BR", currency="BRL",
                       product_type="lowticket", start_date="2026-09-28", end_date="2026-11-22")
CONTEXT = CollectionContext("a", "r", NOW + timedelta(minutes=12), lambda: NOW, "chave-fake")


async def dns(host):
    return ["192.168.1.4"] if host == "interno.example.org" else ["93.184.215.14"]


@pytest.mark.asyncio
async def test_firecrawl_localized_search_and_bounded_scrape():
    calls = []

    def handle(request):
        payload = json.loads(request.content)
        calls.append((request.url.path, payload))
        assert request.headers["Authorization"] == "Bearer chave-fake"
        if request.url.path == "/v2/search":
            return httpx.Response(200, json={"success": True, "data": {"web": [
                {"url": "https://interno.example.org/privado", "title": "Interno"},
                {"url": "file:///etc/hosts", "title": "Arquivo"},
                *[{"url": f"https://example.org/artigo/{i}?token=segredo", "title": f"Artigo {i}"}
                  for i in range(6)],
            ]}})
        return httpx.Response(200, json={
            "success": True, "data": {"markdown": "<p>Trecho público</p>", "rawHtml": "<script>x</script>"},
        })

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        result = await FirecrawlCollector(client, resolver=dns).collect(INPUT, CONTEXT)
    search, *scrapes = calls
    assert search[1]["query"] == INPUT.query
    assert search[1]["country"] == "BR"
    assert search[1]["limit"] == 5
    assert len(scrapes) == len(result.items) == 3
    assert [call[1]["url"] for call in scrapes] == [f"https://example.org/artigo/{i}" for i in range(3)]
    assert all(item.data.excerpt == "Trecho público" for item in result.items)
    assert all(text not in result.model_dump_json() for text in ["<script>", "segredo", "192.168"])
    assert result.scope == "BR"


@pytest.mark.asyncio
@pytest.mark.parametrize(("response", "status", "note"), [
    (401, "error", "credencial"), (429, "error", "limite"), (None, "error", "tempo"),
    (200, "empty", None),
])
async def test_provider_errors_are_distinct_from_empty(response, status, note):
    def handle(request):
        if response is None:
            raise httpx.ReadTimeout("segredo", request=request)
        return httpx.Response(response, json={"success": response == 200, "data": {"web": []}})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handle)) as client:
        result = await FirecrawlCollector(client, resolver=dns).collect(INPUT, CONTEXT)
    assert result.status == status
    assert result.items == []
    if note:
        assert note in " ".join(result.limits.notes).lower()
    assert "segredo" not in result.model_dump_json()
