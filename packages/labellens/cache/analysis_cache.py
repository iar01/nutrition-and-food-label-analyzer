"""Domain-level analysis cache service."""

from __future__ import annotations

import logging
from typing import Any

from labellens.api.schemas import AnalysisOut
from labellens.cache.keys import make_analysis_cache_key
from labellens.cache.store import InMemoryTTLStore

logger = logging.getLogger("labellens.cache")


class AnalysisCache:
    """Manages caching of full AnalysisOut structures for products and profiles."""

    def __init__(self, store: InMemoryTTLStore | None = None) -> None:
        self.store = store or InMemoryTTLStore(default_ttl_seconds=86400)
        self.hits = 0
        self.misses = 0

    def get(self, barcode: str, profile: dict[str, Any] | None) -> AnalysisOut | None:
        key = make_analysis_cache_key(barcode, profile)
        data = self.store.get(key)
        if data is not None:
            self.hits += 1
            logger.info("Cache HIT for %s", key)
            return AnalysisOut.model_validate(data)
        self.misses += 1
        logger.debug("Cache MISS for %s", key)
        return None

    def set(self, barcode: str, profile: dict[str, Any] | None, analysis: AnalysisOut) -> None:
        key = make_analysis_cache_key(barcode, profile)
        self.store.set(key, analysis.model_dump())
        logger.info("Cached analysis for %s (TTL 24h)", key)
