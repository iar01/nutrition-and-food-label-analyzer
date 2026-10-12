"""Unit tests for LabelLens configuration management."""

from labellens.config import Settings, get_settings


def test_default_settings() -> None:
    """Verify that default settings load with expected values."""
    settings = Settings()
    assert settings.postgres_port == 5432
    assert settings.qdrant_port == 6333
    assert "postgresql" in settings.database_url
    assert "http" in settings.qdrant_url
    assert settings.llm_base_url.endswith("/v1")
    assert settings.llm_temperature == 0.2
    assert settings.text_embedding_model == "BAAI/bge-small-en-v1.5"
    assert settings.image_embedding_model == "ViT-B-32"


def test_settings_singleton(test_settings: Settings) -> None:
    """Verify that get_settings() returns a cached instance."""
    s1 = get_settings()
    s2 = get_settings()
    assert s1 is s2
    assert s1.app_env == "test"
    assert s1.postgres_db == "test_labellens"


def test_settings_custom_override() -> None:
    """Verify explicit parameters override default config values."""
    custom = Settings(
        POSTGRES_DB="custom_db",
        POSTGRES_PORT=5433,
        LLM_MODEL="qwen3:8b",
        LLM_TEMPERATURE=0.1,
    )
    assert custom.postgres_db == "custom_db"
    assert custom.postgres_port == 5433
    assert custom.llm_model == "qwen3:8b"
    assert custom.llm_temperature == 0.1
