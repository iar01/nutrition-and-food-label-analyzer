"""Unit tests for OpenAI-compatible LLM client factory."""

from labellens.config import Settings
from labellens.llm.client import get_async_llm_client, get_llm_client


def test_get_llm_client_instantiation() -> None:
    """Verify that sync LLM client is created with configured settings."""
    settings = Settings(
        LLM_BASE_URL="http://localhost:11434/v1",
        LLM_API_KEY="test-key",
        LLM_TIMEOUT_SECONDS=30.0,
    )
    client = get_llm_client(settings)
    assert str(client.base_url).rstrip("/") == "http://localhost:11434/v1"
    assert client.api_key == "test-key"
    assert client.timeout == 30.0


def test_get_async_llm_client_instantiation() -> None:
    """Verify that async LLM client is created with configured settings."""
    settings = Settings(
        LLM_BASE_URL="https://api.openai.com/v1",
        LLM_API_KEY="cloud-key",
        LLM_TIMEOUT_SECONDS=45.0,
    )
    client = get_async_llm_client(settings)
    assert str(client.base_url).rstrip("/") == "https://api.openai.com/v1"
    assert client.api_key == "cloud-key"
    assert client.timeout == 45.0
