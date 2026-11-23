"""Registro dos coletores do Radar."""
from collections.abc import Mapping

from app.services.radar_collectors.base import Collector

CollectorRegistry = Mapping[str, Collector]
