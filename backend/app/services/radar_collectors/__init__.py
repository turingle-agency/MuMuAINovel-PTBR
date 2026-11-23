"""Registro dos coletores do Radar."""
from collections.abc import Mapping

from app.services.radar_collectors.base import Collector

CollectorRegistry = Mapping[str, Collector]

from app.services.radar_collectors.firecrawl import FirecrawlCollector
from app.services.radar_collectors.youtube import YouTubeCommentsCollector

__all__ = ["CollectorRegistry", "FirecrawlCollector", "YouTubeCommentsCollector"]
