import logging
import re
import time
import uuid

from starlette.datastructures import MutableHeaders
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from labellens.api.logging_setup import request_id_var

logger = logging.getLogger("labellens.api")
VALID_ID = re.compile(r"^[A-Za-z0-9._-]{8,64}$")


class RequestContextMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        incoming = ""
        for key, value in scope["headers"]:
            if key == b"x-request-id":
                incoming = value.decode(errors="ignore")
        request_id = incoming if VALID_ID.match(incoming) else uuid.uuid4().hex

        token = request_id_var.set(request_id)
        started_at = time.perf_counter()
        status = 500
        response_started = False

        async def send_with_id(message: Message) -> None:
            nonlocal status, response_started
            if message["type"] == "http.response.start":
                response_started = True
                status = message["status"]
                MutableHeaders(scope=message)["X-Request-ID"] = request_id
            await send(message)

        try:
            await self.app(scope, receive, send_with_id)
        except Exception:
            logger.exception("unhandled error")
            if not response_started:
                status = 500
                body = {
                    "error": "internal_error",
                    "message": "Something went wrong.",
                    "request_id": request_id,
                }
                response = JSONResponse(body, status_code=500, headers={"X-Request-ID": request_id})
                await response(scope, receive, send)
        finally:
            logger.info(
                "request",
                extra={
                    "method": scope["method"],
                    "path": scope["path"],  # no query string: it can contain personal choices
                    "status": status,
                    "duration_ms": round((time.perf_counter() - started_at) * 1000, 1),
                },
            )
            request_id_var.reset(token)
