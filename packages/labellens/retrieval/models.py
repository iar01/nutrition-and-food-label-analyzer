from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class InputType(StrEnum):
    BARCODE = "barcode"
    TEXT = "text"
    PRODUCT_IMAGE = "product_image"
    LABEL_IMAGE = "label_image"
    KNOWLEDGE = "knowledge"


class SearchHit(BaseModel):
    """A single retrieved item."""

    id: str
    code: str
    name: str
    brand: str | None = None
    score: float = Field(description="Relevance or retrieval score")
    rank: int = Field(description="1-based rank in final results")
    match_source: str = Field(
        description="e.g. 'postgres_exact', 'hybrid_rrf', 'clip_visual', 'reranked'"
    )
    payload: dict[str, Any] = Field(default_factory=dict)


class SearchResponse(BaseModel):
    """The unified container returned by search()."""

    query: str
    input_type: InputType
    hits: list[SearchHit]
    total_found: int
    latency_ms: float
    filters_applied: dict[str, Any] | None = None
