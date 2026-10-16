"""In-memory cache store with Time-To-Live (TTL) expiration."""

from __future__ import annotations

import threading
import time
from typing import Any


class InMemoryTTLStore:
    """Simple, thread-safe in-memory cache with TTL expiration.

    No Redis required for single-instance or local setups, but follows
    the same interface so we can swap to Redis in the future.
    """

    def __init__(self, default_ttl_seconds: int = 86400, max_entries: int = 10000) -> None:
        self.default_ttl = default_ttl_seconds
        self.max_entries = max_entries
        self._store: dict[str, tuple[float, Any]] = {}  # key -> (expires_at, value)
        self._lock = threading.Lock()

    def get(self, key: str) -> Any | None:
        """Retrieve a value if present and not expired."""
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            expires_at, val = entry
            if time.time() > expires_at:
                del self._store[key]
                return None
            return val

    def set(self, key: str, value: Any, ttl_seconds: int | None = None) -> None:
        """Store a value with an expiration timestamp."""
        ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        expires_at = time.time() + ttl
        with self._lock:
            # Evict oldest entry if at capacity
            if len(self._store) >= self.max_entries and key not in self._store:
                oldest_key = next(iter(self._store))
                del self._store[oldest_key]
            self._store[key] = (expires_at, value)

    def delete(self, key: str) -> None:
        """Remove a specific key from cache."""
        with self._lock:
            self._store.pop(key, None)

    def clear(self) -> None:
        """Empty the cache."""
        with self._lock:
            self._store.clear()

    def __len__(self) -> int:
        return len(self._store)
