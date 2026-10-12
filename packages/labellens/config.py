"""Application configuration management using Pydantic Settings."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration for LabelLens services and pipelines."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application Environment
    app_env: Literal["development", "staging", "production", "test"] = Field(
        default="development",
        alias="APP_ENV",
    )
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # PostgreSQL Configuration
    postgres_user: str = Field(default="postgres", alias="POSTGRES_USER")
    postgres_password: str = Field(default="postgres", alias="POSTGRES_PASSWORD")
    postgres_db: str = Field(default="labellens", alias="POSTGRES_DB")
    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/labellens",
        alias="DATABASE_URL",
    )
    sync_database_url: str = Field(
        default="postgresql://postgres:postgres@localhost:5432/labellens",
        alias="SYNC_DATABASE_URL",
    )

    # Qdrant Vector Database
    qdrant_host: str = Field(default="localhost", alias="QDRANT_HOST")
    qdrant_port: int = Field(default=6333, alias="QDRANT_PORT")
    qdrant_grpc_port: int = Field(default=6334, alias="QDRANT_GRPC_PORT")
    qdrant_url: str = Field(default="http://localhost:6333", alias="QDRANT_URL")
    qdrant_api_key: str | None = Field(default=None, alias="QDRANT_API_KEY")

    # LLM Configuration (OpenAI-compatible)
    llm_base_url: str = Field(default="http://localhost:11434/v1", alias="LLM_BASE_URL")
    llm_model: str = Field(default="qwen2.5:7b", alias="LLM_MODEL")
    llm_api_key: str = Field(default="ollama", alias="LLM_API_KEY")
    llm_temperature: float = Field(default=0.2, alias="LLM_TEMPERATURE")
    llm_timeout_seconds: float = Field(default=60.0, alias="LLM_TIMEOUT_SECONDS")

    # Embedding & Reranker Models
    text_embedding_model: str = Field(
        default="BAAI/bge-small-en-v1.5",
        alias="TEXT_EMBEDDING_MODEL",
    )
    image_embedding_model: str = Field(
        default="ViT-B-32",
        alias="IMAGE_EMBEDDING_MODEL",
    )
    image_embedding_pretrained: str = Field(
        default="openai",
        alias="IMAGE_EMBEDDING_PRETRAINED",
    )
    sparse_embedding_model: str = Field(
        default="Qdrant/bm25",
        alias="SPARSE_EMBEDDING_MODEL",
    )
    reranker_model: str = Field(
        default="BAAI/bge-reranker-base",
        alias="RERANKER_MODEL",
    )

    # Observability
    langsmith_tracing: bool = Field(default=False, alias="LANGSMITH_TRACING")
    langsmith_api_key: str | None = Field(default=None, alias="LANGSMITH_API_KEY")
    langsmith_project: str = Field(default="labellens", alias="LANGSMITH_PROJECT")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()
