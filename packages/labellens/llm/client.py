"""Provider-agnostic OpenAI-compatible LLM client factory."""

from langchain_openai import ChatOpenAI
from openai import AsyncOpenAI, OpenAI
from pydantic import SecretStr

from labellens.config import Settings, get_settings, settings


def get_llm_client(settings: Settings | None = None) -> OpenAI:
    """Return a synchronous OpenAI-compatible client.

    Uses `LLM_BASE_URL` and `LLM_API_KEY` from settings to support local Ollama
    as well as cloud providers without code changes.
    """
    cfg = settings or get_settings()
    return OpenAI(
        base_url=cfg.llm_base_url,
        api_key=cfg.llm_api_key,
        timeout=cfg.llm_timeout_seconds,
    )


def get_async_llm_client(settings: Settings | None = None) -> AsyncOpenAI:
    """Return an asynchronous OpenAI-compatible client."""
    cfg = settings or get_settings()
    return AsyncOpenAI(
        base_url=cfg.llm_base_url,
        api_key=cfg.llm_api_key,
        timeout=cfg.llm_timeout_seconds,
    )


def get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.llm_model,
        base_url=settings.llm_base_url,
        api_key=SecretStr(settings.llm_api_key),
        temperature=settings.llm_temperature,
        timeout=settings.llm_timeout_seconds,
        max_retries=1,
    )
