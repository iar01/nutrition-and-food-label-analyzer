"""Semantic vector cache for conversational product questions (Tier 2)."""

from __future__ import annotations

import logging
import threading
import time
from dataclasses import dataclass, field
from typing import Any

from labellens.cache.keys import hash_profile

logger = logging.getLogger("labellens.cache")


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two float vectors."""
    dot = sum(x * y for x, y in zip(a, b, strict=False))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(x * x for x in b) ** 0.5
    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0
    return float(dot / (norm_a * norm_b))


@dataclass
class SemanticHit:
    answer: str
    similarity: float
    matched_query: str
    analysis: dict[str, Any] | None = None


@dataclass
class SemanticEntry:
    vector: list[float]
    query: str
    product_code: str
    profile_hash: str
    answer: str
    expires_at: float
    metadata: dict[str, Any] = field(default_factory=dict)


class SemanticCache:
    """Vector-based semantic cache for natural language product questions."""

    def __init__(
        self,
        similarity_threshold: float = 0.92,
        default_ttl_seconds: int = 604800,  # 7 days
        max_entries: int = 5000,
    ) -> None:
        self.similarity_threshold = similarity_threshold
        self.default_ttl = default_ttl_seconds
        self.max_entries = max_entries
        self._entries: list[SemanticEntry] = []
        self._lock = threading.Lock()
        self.hits = 0
        self.misses = 0

    def get(
        self,
        query: str,
        product_code: str,
        profile: dict[str, Any] | None,
        query_vector: list[float] | None = None,
        embedder: Any = None,
        threshold: float | None = None,
    ) -> SemanticHit | None:
        """Find a cached answer matching query semantics for the same product and profile."""
        p_hash = hash_profile(profile)
        code = product_code.strip()
        min_sim = threshold if threshold is not None else self.similarity_threshold

        now = time.time()
        with self._lock:
            # Quick candidate pre-filter by product and profile
            candidates = [
                e
                for e in self._entries
                if e.product_code == code and e.profile_hash == p_hash and e.expires_at > now
            ]

        if not candidates:
            self.misses += 1
            return None

        # Compute query vector if not supplied
        vector = query_vector
        if vector is None and embedder is not None:
            if hasattr(embedder, "embed_query"):
                vector = list(embedder.embed_query(query))
            elif hasattr(embedder, "embed_text"):
                vector = list(embedder.embed_text([query])[0])

        if vector is None:
            self.misses += 1
            return None

        best_hit: SemanticEntry | None = None
        best_sim = -1.0

        for candidate in candidates:
            sim = cosine_similarity(vector, candidate.vector)
            if sim > best_sim:
                best_sim = sim
                best_hit = candidate

        if best_hit is not None and best_sim >= min_sim:
            with self._lock:
                self.hits += 1
            logger.info(
                "SemanticCache HIT (score=%.3f, matched='%s' for query='%s')",
                best_sim,
                best_hit.query,
                query,
            )
            return SemanticHit(
                answer=best_hit.answer,
                similarity=best_sim,
                matched_query=best_hit.query,
                analysis=best_hit.metadata.get("analysis"),
            )

        with self._lock:
            self.misses += 1
        return None

    def set(
        self,
        query: str,
        product_code: str,
        profile: dict[str, Any] | None,
        answer: str,
        vector: list[float] | None = None,
        embedder: Any = None,
        ttl_seconds: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Store a question, embedding vector, and verified answer."""
        if vector is None and embedder is not None:
            if hasattr(embedder, "embed_query"):
                vector = list(embedder.embed_query(query))
            elif hasattr(embedder, "embed_text"):
                vector = list(embedder.embed_text([query])[0])

        if vector is None:
            logger.warning("SemanticCache.set called without vector or embedder; skipping entry.")
            return

        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        entry = SemanticEntry(
            vector=vector,
            query=query.strip(),
            product_code=product_code.strip(),
            profile_hash=hash_profile(profile),
            answer=answer,
            expires_at=time.time() + ttl,
            metadata=metadata or {},
        )

        with self._lock:
            if len(self._entries) >= self.max_entries:
                self._entries.pop(0)  # Evict oldest entry
            self._entries.append(entry)
            logger.info("SemanticCache stored query for product %s", product_code)

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()
            self.hits = 0
            self.misses = 0

    def __len__(self) -> int:
        return len(self._entries)
