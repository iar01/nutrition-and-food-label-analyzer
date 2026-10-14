"""Application configuration management using Pydantic Settings."""

import uuid
from functools import lru_cache
from pathlib import Path
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

    # Qdrant collections
    products_collection: str = Field(default="products", alias="PRODUCTS_COLLECTION")
    knowledge_collection: str = Field(default="knowledge", alias="KNOWLEDGE_COLLECTION")

    # Data paths
    clean_products_path: Path = Field(
        default=Path("data/clean/products.parquet"), alias="CLEAN_PRODUCTS_PATH"
    )
    images_dir: Path = Field(default=Path("data/images"), alias="IMAGES_DIR")
    image_keys_path: Path = Field(default=Path("data/raw/data_keys.gz"), alias="IMAGE_KEYS_PATH")
    embeddings_dir: Path = Field(default=Path("data/embeddings"), alias="EMBEDDINGS_DIR")

    # Compatibility aliases
    @property
    def text_embed_model(self) -> str:
        return self.text_embedding_model

    @property
    def image_embed_model(self) -> str:
        return self.image_embedding_model

    @property
    def image_embed_pretrained(self) -> str:
        return self.image_embedding_pretrained

    @property
    def sparse_embed_model(self) -> str:
        return self.sparse_embedding_model


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings singleton."""
    return Settings()


def point_id(code: str) -> str:
    """Same barcode -> same ID, every time. This makes re-running jobs safe (idempotent)."""
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"labellens:product:{code}"))


settings = get_settings()
