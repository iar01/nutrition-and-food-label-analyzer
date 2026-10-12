"""Integration tests for infrastructure services (Postgres and Qdrant)."""

import pytest
from labellens.config import get_settings
from qdrant_client import QdrantClient
from sqlalchemy import create_engine, text


@pytest.mark.integration
def test_postgres_connectivity() -> None:
    """Verify that PostgreSQL is healthy and queries can execute."""
    settings = get_settings()
    engine = create_engine(settings.sync_database_url)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1")).scalar()
        assert result == 1


@pytest.mark.integration
def test_qdrant_connectivity() -> None:
    """Verify that Qdrant is healthy and responding over HTTP."""
    settings = get_settings()
    client = QdrantClient(url=settings.qdrant_url, timeout=5)
    collections = client.get_collections()
    assert collections is not None
