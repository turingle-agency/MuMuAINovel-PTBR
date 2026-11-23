"""Amostra de vídeos e comentários públicos de nível superior no YouTube."""
from datetime import timedelta
import re

import httpx

from app.schemas.radar import CollectorInput, EvidenceItem, SourceResult, SourceStatus
from app.services.radar_collectors.base import (
    CollectionContext, CollectionError, observed_date, provider_json, text_excerpt,
)

URL = "https://www.googleapis.com/youtube/v3"
VIDEO_LIMIT = 5
COMMENT_LIMIT = 10


def _resource_id(value) -> str | None:
    return value if isinstance(value, str) and re.fullmatch(r"[\w-]{1,120}", value, re.ASCII) else None


def _items(data):
    items = data.get("items")
    if not isinstance(items, list):
        raise CollectionError("O YouTube retornou um formato inesperado.")
    return items


class YouTubeCommentsCollector:
    def __init__(self, http: httpx.AsyncClient):
        self.http = http

    async def collect(self, input: CollectorInput, context: CollectionContext) -> SourceResult:
        notes = [
            "A região orienta a busca de vídeos. O país dos autores dos comentários é desconhecido.",
            "Amostra de até 5 vídeos e 10 comentários públicos de nível superior por vídeo.",
        ]
        items = []
        status: SourceStatus = "not_configured"
        if context.credential:
            headers = {"x-goog-api-key": context.credential}
            try:
                rows = await self._search(input, context, headers)
                status = await self._sample(rows, items, notes, context, headers)
            except CollectionError as error:
                status = "error"
                notes.append(str(error))
        else:
            notes.append("Cadastre a chave da API de Dados do YouTube para coletar.")
        return SourceResult(
            source="youtube", status=status, collected_at=context.clock(), scope=input.country,
            method_version="youtube-data-v3-1", items=items,
            limits={"sample_limit": VIDEO_LIMIT, "exhausted": status == "empty", "notes": notes},
        )

    async def _search(self, input, context, headers):
        result = await provider_json(self.http, context, "GET", f"{URL}/search", headers=headers, params={
            "part": "snippet", "q": input.query, "type": "video", "maxResults": VIDEO_LIMIT,
            "regionCode": input.country, "relevanceLanguage": input.language.split("-")[0],
            "publishedAfter": f"{input.start_date}T00:00:00Z",
            "publishedBefore": f"{input.end_date + timedelta(days=1)}T00:00:00Z",
            "fields": "items(id/videoId,snippet(title,publishedAt))",
        })
        return _items(result)

    async def _sample(self, rows, items, notes, context, headers):
        if not rows:
            return "empty"
        partial = False
        seen = set()
        for row in rows[:VIDEO_LIMIT]:
            identifier = row.get("id") if isinstance(row, dict) else None
            video_id = _resource_id(identifier.get("videoId")) if isinstance(identifier, dict) else None
            if not video_id:
                partial = True
                continue
            if video_id in seen:
                continue
            seen.add(video_id)
            snippet = row.get("snippet") if isinstance(row.get("snippet"), dict) else {}
            link = f"https://www.youtube.com/watch?v={video_id}"
            title = text_excerpt(snippet.get("title"), context.credential) or "Vídeo do YouTube"
            items.append(EvidenceItem(
                id=f"video:{video_id}", kind="content", url=link, label=title,
                observed_date=observed_date(snippet.get("publishedAt")),
            ))
            try:
                items.extend(await self._comments(video_id, link, context, headers))
            except CollectionError as error:
                partial = True
                notes.append(str(error))
        if not items:
            notes.append("A busca retornou vídeos sem identificador válido.")
            return "error"
        return "partial" if partial else "ok"

    async def _comments(self, video_id, link, context, headers):
        payload = await provider_json(self.http, context, "GET", f"{URL}/commentThreads", headers=headers, params={
            "part": "snippet", "videoId": video_id, "maxResults": COMMENT_LIMIT, "textFormat": "plainText",
            "order": "relevance",
            "fields": "items(snippet/topLevelComment(id,snippet(textDisplay,publishedAt)))",
        })
        items = []
        for row in _items(payload)[:COMMENT_LIMIT]:
            try:
                comment = row["snippet"]["topLevelComment"]
                identifier = _resource_id(comment["id"])
                snippet = comment["snippet"]
                excerpt = text_excerpt(snippet["textDisplay"], context.credential)
            except (KeyError, TypeError):
                continue
            if identifier and excerpt:
                items.append(EvidenceItem(
                    id=f"comment:{identifier}", kind="content", label="Comentário público",
                    url=f"{link}&lc={identifier}", observed_date=observed_date(snippet.get("publishedAt")),
                    data={"excerpt": excerpt},
                ))
        return items
