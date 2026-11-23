"""Registro dos coletores do Radar."""
from collections.abc import Mapping
from httpx import AsyncClient

from app.services.radar_collectors.base import Collector
from app.services.radar_collectors.firecrawl import FirecrawlCollector
from app.services.radar_collectors.youtube import YouTubeCommentsCollector

CollectorRegistry = Mapping[str, Collector]


def build_registry(http: AsyncClient) -> CollectorRegistry:
    return {"firecrawl": FirecrawlCollector(http), "youtube": YouTubeCommentsCollector(http)}
