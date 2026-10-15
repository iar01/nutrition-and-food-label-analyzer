from typing import Literal

from pydantic import BaseModel, Field


class RouterDecision(BaseModel):
    input_kind: Literal["barcode", "text", "other"]
    barcode: str | None = None
    product_query: str | None = None
    wants_alternatives: bool = False


class Notable(BaseModel):
    item: str
    why: str
    evidence_ids: list[str] = Field(default_factory=list)


class IngredientFindings(BaseModel):
    notable: list[Notable] = Field(default_factory=list)
    summary: str


class AdditiveNote(BaseModel):
    e_number: str
    explanation: str
    relevant_to_user: str | None = None
    evidence_id: str


class AdditiveFindings(BaseModel):
    notes: list[AdditiveNote] = Field(default_factory=list)


class FinalSummary(BaseModel):
    summary: str
    tips: list[str] = Field(default_factory=list)
