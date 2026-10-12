"""Pytest test configuration and fixtures."""

import os
from collections.abc import Generator

import pytest
from labellens.config import Settings, get_settings


@pytest.fixture
def test_settings() -> Generator[Settings, None, None]:
    """Provide isolated Settings instance for unit tests."""
    original_env = dict(os.environ)
    # Ensure test environment overrides
    os.environ["APP_ENV"] = "test"
    os.environ["POSTGRES_DB"] = "test_labellens"
    os.environ["POSTGRES_HOST"] = "localhost"
    os.environ["POSTGRES_PORT"] = "5432"
    os.environ["QDRANT_HOST"] = "localhost"
    os.environ["QDRANT_PORT"] = "6333"

    # Invalidate cache and create fresh settings
    get_settings.cache_clear()
    settings = get_settings()

    yield settings

    os.environ.clear()
    os.environ.update(original_env)
    get_settings.cache_clear()
