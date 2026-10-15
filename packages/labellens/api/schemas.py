from typing import Annotated, Literal

from pydantic import BaseModel, Field, model_validator

from labellens.agents.schemas import AdditiveNote, IngredientFindings
from labellens.agents.types import Allergen, Diet, Goal

Barcode = Annotated[
    str,
    Field(pattern=r"^\d{8,14}$", description="Product barcode (EAN or UPC), 8 to 14 digits."),
]


# ------------------------------------------------------------------ requests
class Profile(BaseModel):
    diets: list[Diet] = Field(default_factory=list, max_length=6)
    allergens: list[Allergen] = Field(default_factory=list, max_length=14)
    goals: list[Goal] = Field(default_factory=list, max_length=3)


class ChatRequest(BaseModel):
    """Start a new analysis with `message`, or resume a paused one with `thread_id` + `resume_code`."""

    message: str | None = Field(default=None, min_length=2, max_length=500)
    thread_id: str | None = Field(default=None, pattern=r"^[A-Za-z0-9-]{8,64}$")
    resume_code: Barcode | None = None
    profile: Profile = Field(default_factory=Profile)
    auto_pick: bool = False

    @model_validator(mode="after")
    def check_mode(self) -> "ChatRequest":
        resuming = bool(self.thread_id and self.resume_code)
        if self.message is None and not resuming:
            raise ValueError("Send either 'message', or 'thread_id' together with 'resume_code'.")
        if self.message is not None and (self.thread_id or self.resume_code):
            raise ValueError("Send either 'message' or 'thread_id' + 'resume_code', not both.")
        return self


class FeedbackIn(BaseModel):
    rating: Literal["up", "down"]
    comment: str | None = Field(default=None, max_length=500)
    request_id: str | None = Field(default=None, max_length=64)
    thread_id: str | None = Field(default=None, max_length=64)
    product_code: Barcode | None = None


# ----------------------------------------------------------------- responses
class ProductSummary(BaseModel):
    code: str
    name: str | None = None
    brand: str | None = None
    quantity: str | None = None
    ingredients: str | None = None
    nutriscore: str | None = None
    nova_group: int | None = None
    categories: list[str] = Field(default_factory=list)
    allergens: list[str] = Field(default_factory=list)
    traces: list[str] = Field(default_factory=list)
    additives: list[str] = Field(default_factory=list)
    nutrition_per_100g: dict[str, float | None] = Field(default_factory=dict)
    off_url: str


class VerdictItem(BaseModel):
    status: str
    reasons: list[str] = Field(default_factory=list)
    evidence_ids: list[str] = Field(default_factory=list)


class NutritionItem(BaseModel):
    value: float | None = None
    level: Literal["low", "medium", "high", "unknown"]


class Verdicts(BaseModel):
    diets: dict[str, VerdictItem]
    allergens: dict[str, VerdictItem]
    nutrition: dict[str, NutritionItem]
    goals: dict[str, str]
    overall: Literal["not_suitable", "check", "no_conflicts_found", "no_profile"]


class AdditiveSection(BaseModel):
    notes: list[AdditiveNote] = Field(default_factory=list)
    missing: list[str] = Field(default_factory=list)


class AlternativeOut(BaseModel):
    code: str
    name: str | None = None
    brand: str | None = None
    nutriscore: str | None = None


class EvidenceOut(BaseModel):
    id: str
    kind: str
    title: str
    text: str
    source_url: str = ""


class AnalysisOut(BaseModel):
    product: ProductSummary
    verdicts: Verdicts
    ingredients: IngredientFindings | None = None
    additives: AdditiveSection | None = None
    alternatives: list[AlternativeOut] = Field(default_factory=list)
    evidence: list[EvidenceOut] = Field(default_factory=list)
    answer_markdown: str


class CandidateOut(BaseModel):
    code: str | None = None
    name: str | None = None
    brands: str | None = None
    nutriscore: str | None = None
    score: float | None = None


class AnalyzeResponse(AnalysisOut):
    matched_by: Literal["barcode", "text", "image"]
    candidates: list[CandidateOut] = Field(default_factory=list)
    thread_id: str
    request_id: str


class SearchHit(BaseModel):
    code: str | None = None
    name: str | None = None
    brands: str | None = None
    nutriscore: str | None = None
    score: float


class SearchResponse(BaseModel):
    count: int
    results: list[SearchHit]


class FeedbackOut(BaseModel):
    id: int


class CheckResult(BaseModel):
    name: str
    ok: bool
    critical: bool


class ReadyOut(BaseModel):
    status: Literal["ok", "degraded", "unavailable"]
    checks: list[CheckResult]


class ErrorOut(BaseModel):
    error: str
    message: str
    request_id: str
