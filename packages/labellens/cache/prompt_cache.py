"""Prompt-level exact response cache (Tier 3)."""

from __future__ import annotations

import hashlib
import logging

from labellens.cache.store import InMemoryTTLStore

logger = logging.getLogger("labellens.cache")


def make_prompt_cache_key(system: str, user: str, schema_name: str = "") -> str:
    """Generate a collision-resistant SHA-256 key for a prompt and schema."""
    content = f"{schema_name}:::{system}:::{user}"
    return f"prompt:{hashlib.sha256(content.encode('utf-8')).hexdigest()}"


class PromptCache:
    """Caches exact structured JSON outputs for repeated prompts and schemas."""

    def __init__(self, store: InMemoryTTLStore | None = None) -> None:
        # Default TTL: 7 days (prompts on static food facts and additives are highly durable)
        self.store = store or InMemoryTTLStore(default_ttl_seconds=604800, max_entries=5000)
        self.hits = 0
        self.misses = 0

    def get(self, system: str, user: str, schema_name: str = "") -> str | None:
        """Retrieve cached JSON string if present."""
        key = make_prompt_cache_key(system, user, schema_name)
        data = self.store.get(key)
        if data is not None:
            self.hits += 1
            logger.info("PromptCache HIT for %s", key)
            return str(data)
        self.misses += 1
        logger.debug("PromptCache MISS for %s", key)
        return None

    def set(self, system: str, user: str, json_text: str, schema_name: str = "") -> None:
        """Store a JSON response for a given prompt and schema."""
        key = make_prompt_cache_key(system, user, schema_name)
        self.store.set(key, json_text)
        logger.info("PromptCache stored %s", key)

    def clear(self) -> None:
        self.store.clear()
        self.hits = 0
        self.misses = 0
