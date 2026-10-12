"""Pydantic schemas and DTOs for database queries and repositories."""

import uuid
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class NutritionDetails(BaseModel):
    """Nutritional values per 100g."""

    model_config = ConfigDict(from_attributes=True)

    energy_kcal: float | None = None
    fat_g: float | None = None
    sat_fat_g: float | None = None
    carbs_g: float | None = None
    sugars_g: float | None = None
    fiber_g: float | None = None
    protein_g: float | None = None
    salt_g: float | None = None
    sodium_g: float | None = None


class AdditiveDetails(BaseModel):
    """Additive catalog entity representation."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str | None = None
    e_number: str | None = None
    short_description: str | None = None


class ProductSummary(BaseModel):
    """Compact product projection for search results and listings."""

    model_config = ConfigDict(from_attributes=True)

    code: str
    name: str
    brand: str | None = None
    quantity: str | None = None
    categories: list[str] | None = None
    nutriscore: str | None = None
    nova: int | None = None
    ecoscore: str | None = None
    completeness: float
    search_text: str | None = None


class ProductDetail(BaseModel):
    """Complete product entity with relations for barcode detail views."""

    model_config = ConfigDict(from_attributes=True)

    code: str
    name: str
    brand: str | None = None
    quantity: str | None = None
    categories: list[str] | None = None
    ingredients_text: str
    nutriscore: str | None = None
    nova: int | None = None
    ecoscore: str | None = None
    completeness: float
    off_url: str | None = None
    quality_flags: list[str] = Field(default_factory=list)
    search_text: str

    nutrition: NutritionDetails | None = None
    additives: list[AdditiveDetails] = Field(default_factory=list)
    allergens: list[dict[str, str]] = Field(default_factory=list)
    diet_flags: dict[str, str] = Field(default_factory=dict)


class UserProfile(BaseModel):
    """User dietary preferences and health goals."""

    model_config = ConfigDict(from_attributes=True)

    user_id: uuid.UUID
    email: str | None = None
    diets: list[str] = Field(default_factory=list)
    allergens: list[str] = Field(default_factory=list)
    goals: dict[str, Any] = Field(default_factory=dict)
