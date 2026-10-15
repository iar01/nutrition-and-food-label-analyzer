from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.concurrency import run_in_threadpool

from labellens.api import routes_analysis, routes_core
from labellens.api.config import ApiConfig
from labellens.api.errors import ApiError, api_error_handler
from labellens.api.logging_setup import setup_logging
from labellens.api.middleware import RequestContextMiddleware
from labellens.api.security import RateLimiter
from labellens.api.services import Services, build_services
from labellens.api.slots import RunSlots
from labellens.config import settings


def create_app(config: ApiConfig | None = None, services: Services | None = None) -> FastAPI:
    config = config or ApiConfig.from_settings(settings)
    if config.env == "production" and not config.api_keys:
        raise RuntimeError("API_KEYS must be set when APP_ENV=production.")
    setup_logging(settings.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        if app.state.services is None:  # the real server builds everything once, at startup
            app.state.services = await run_in_threadpool(build_services)
        yield

    app = FastAPI(
        title="LabelLens API",
        version="0.1.0",
        description="Analyse packaged food: allergens, diets, additives and alternatives. "
        "Data from Open Food Facts (ODbL). General information, not medical advice.",
        lifespan=lifespan,
    )
    app.state.config = config
    app.state.services = services
    app.state.limiter = RateLimiter(config.rate_limit_per_minute)
    app.state.run_slots = RunSlots(config.max_concurrent_runs)

    app.add_exception_handler(ApiError, api_error_handler)
    # The last middleware added is the outermost one.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(config.cors_origins),
        allow_methods=["GET", "POST"],
        allow_headers=["X-API-Key", "Content-Type", "X-Request-ID"],
        expose_headers=["X-Request-ID"],
    )
    app.add_middleware(RequestContextMiddleware)

    app.include_router(routes_core.public)
    app.include_router(routes_core.v1)
    app.include_router(routes_analysis.router)
    return app
