import hmac
import time
from collections import defaultdict, deque

from fastmcp import FastMCP
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send


class AuthAndRateLimit:
    def __init__(self, app: ASGIApp, token: str | None, max_per_minute: int = 120) -> None:
        self.app = app
        self.token = token
        self.max_per_minute = max_per_minute
        self.hits: dict[str, deque[float]] = defaultdict(deque)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":  # lifespan events pass straight through
            await self.app(scope, receive, send)
            return

        headers = {k.decode().lower(): v.decode(errors="ignore") for k, v in scope["headers"]}
        supplied = headers.get("authorization", "")

        if self.token is not None:
            expected = f"Bearer {self.token}"
            if not hmac.compare_digest(supplied.encode(), expected.encode()):
                await JSONResponse({"error": "unauthorized"}, status_code=401)(scope, receive, send)
                return

        caller = supplied or (scope.get("client") or ("anonymous", 0))[0]
        now = time.monotonic()
        window = self.hits[caller]
        while window and now - window[0] > 60:
            window.popleft()
        if len(window) >= self.max_per_minute:
            response = JSONResponse(
                {"error": "rate_limited"}, status_code=429, headers={"Retry-After": "30"}
            )
            await response(scope, receive, send)
            return
        window.append(now)

        await self.app(scope, receive, send)


def build_http_app(mcp: FastMCP, token: str | None, max_per_minute: int = 120) -> ASGIApp:
    return AuthAndRateLimit(mcp.http_app(path="/mcp"), token, max_per_minute)
