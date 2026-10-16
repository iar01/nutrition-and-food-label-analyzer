"""Cache key generators with deterministic profile hashing."""

from __future__ import annotations

import hashlib
import json
from typing import Any


def hash_profile(profile: dict[str, Any] | None) -> str:
    """Produce a deterministic SHA-256 fingerprint for a dietary profile.

    Lists (diets, allergens, goals) are sorted so order does not affect the hash:
    ['milk', 'egg'] produces the exact same hash as ['egg', 'milk'].
    """
    if not profile:
        return "default"

    # Normalize by sorting all list values and omitting empty collections
    normalized = {}
    for key in sorted(profile.keys()):
        val = profile[key]
        if val is None or val == [] or val == {} or val == "":
            continue
        if isinstance(val, list):
            normalized[key] = sorted(val)
        else:
            normalized[key] = val

    if not normalized:
        return "default"

    canonical_json = json.dumps(normalized, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()[:16]


def make_analysis_cache_key(barcode: str, profile: dict[str, Any] | None) -> str:
    """Generate a cache key for product analysis."""
    p_hash = hash_profile(profile)
    # Normalize barcode (strip whitespace, ensure digits)
    clean_code = barcode.strip()
    return f"analysis:{clean_code}:{p_hash}"
