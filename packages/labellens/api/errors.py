from fastapi import Request
from fastapi.responses import JSONResponse

from labellens.api.logging_setup import request_id_var
from labellens.api.schemas import ErrorOut


class ApiError(Exception):
    def __init__(
        self, status_code: int, code: str, message: str, headers: dict[str, str] | None = None
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.headers = headers


async def api_error_handler(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, ApiError)
    body = ErrorOut(error=exc.code, message=exc.message, request_id=request_id_var.get())
    return JSONResponse(body.model_dump(), status_code=exc.status_code, headers=exc.headers)
