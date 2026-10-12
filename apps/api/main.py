"""FastAPI gateway application entrypoint."""

from typing import Any

from labellens.config import get_settings


def create_app() -> Any:
    """Application factory for FastAPI gateway."""
    try:
        from fastapi import FastAPI
    except ImportError:
        # FastAPI will be added in Phase 8
        return None

    settings = get_settings()
    app = FastAPI(
        title="LabelLens API Gateway",
        description="Nutritional and food label analysis API",
        version="0.1.0",
    )

    @app.get("/health")
    def health_check() -> dict[str, str]:
        """Liveness probe."""
        return {"status": "ok", "env": settings.app_env}

    @app.get("/ready")
    def readiness_check() -> dict[str, str]:
        """Readiness probe."""
        return {"status": "ready"}

    return app


app = create_app()
