import hashlib
import hmac
import time
from collections import defaultdict, deque
from typing import Annotated

from fastapi import Header, Request

from labellens.api.config import ApiConfig
from labellens.api.errors import ApiError


class RateLimiter:
    """Fixed sliding window per caller. One process only; a real deployment would use Redis."""

    def __init__(self, max_per_minute: int) -> None:
        self.max_per_minute = max_per_minute
        self.hits: dict[str, deque[float]] = defaultdict(deque)

    def check(self, caller: str) -> None:
        now = time.monotonic()
        window = self.hits[caller]
        while window and now - window[0] > 60:
            window.popleft()
        if len(window) >= self.max_per_minute:
            retry_after = max(1, int(60 - (now - window[0])))
            raise ApiError(
                429,
                "rate_limited",
                "Too many requests, slow down.",
                headers={"Retry-After": str(retry_after)},
            )
        window.append(now)


def check_api_key(config: ApiConfig, supplied: str | None) -> str:
    """Return a stable, non-secret id for the caller, or raise 401."""
    if not config.api_keys:  # development mode without keys
        return "anonymous"
    ok = False
    for key in config.api_keys:  # compare against every key so timing does not reveal which matched
        ok |= hmac.compare_digest((supplied or "").encode(), key.encode())
    if not ok:
        raise ApiError(
            401,
            "unauthorized",
            "Missing or invalid API key.",
            headers={"WWW-Authenticate": "ApiKey"},
        )
    return hashlib.sha256((supplied or "").encode()).hexdigest()[:16]


async def guard(request: Request, x_api_key: Annotated[str | None, Header()] = None) -> str:
    config: ApiConfig = request.app.state.config
    caller = check_api_key(config, x_api_key)
    if caller == "anonymous":
        caller = request.client.host if request.client else "unknown"
    request.app.state.limiter.check(caller)
    return caller
