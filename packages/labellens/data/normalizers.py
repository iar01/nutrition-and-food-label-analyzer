"""Text normalization and search card construction utilities."""

import math
import re
import unicodedata
from typing import Any

# Precompiled regex for stripping HTML/markup tags
HTML_TAG_RE = re.compile(r"<[^>]+>")
WHITESPACE_RE = re.compile(r"\s+")


def normalize_text(text: Any) -> str:
    """Normalize text using Unicode NFKC, strip HTML tags, and collapse whitespace."""
    if not isinstance(text, str) or not text.strip():
        return ""

    # Strip HTML tags (e.g. <span class="allergen">...</span>)
    no_html = HTML_TAG_RE.sub(" ", text)

    # Unicode NFKC normalization
    nfkc_text = unicodedata.normalize("NFKC", no_html)

    # Collapse multiple whitespaces and trim
    cleaned = WHITESPACE_RE.sub(" ", nfkc_text).strip()
    return cleaned


def clean_ingredients_text(text: str | None) -> str:
    """Clean and normalize raw ingredients text string."""
    cleaned = normalize_text(text)
    # Remove leading labels like "Ingredients:" or "Ingrédients :"
    cleaned = re.sub(
        r"^(?:ingredients?|ingrédients?|zutaten)\s*[:\-]\s*", "", cleaned, flags=re.IGNORECASE
    )
    return cleaned.strip()


def build_search_text(row: dict[str, Any]) -> str:
    """Build a rich, structured textual card for embedding and hybrid search.

    Includes key product identity, brand, categories, ingredients, allergens,
    additives, scores, and per-100g macro nutrients.
    """
    name = row.get("name")
    name_str = str(name).strip() if isinstance(name, str) and name.strip() else "Unknown Product"

    brand = row.get("brand")
    brand_str = str(brand).strip() if isinstance(brand, str) and brand.strip() else "Unknown Brand"

    categories = row.get("categories") or row.get("categories_tags")
    if isinstance(categories, (list, tuple)):
        categories_str = ", ".join(
            str(c).replace("en:", "").replace("-", " ") for c in categories[:5]
        )
    elif isinstance(categories, str) and categories.strip():
        categories_str = categories.strip()
    else:
        categories_str = "None"

    ingredients = row.get("ingredients")
    ingredients_str = (
        str(ingredients).strip()
        if isinstance(ingredients, str) and ingredients.strip()
        else "No ingredients listed"
    )

    allergens = row.get("allergens") or row.get("allergens_tags")
    if isinstance(allergens, (list, tuple)):
        allergens_str = ", ".join(str(a).replace("en:", "").replace("-", " ") for a in allergens)
    elif isinstance(allergens, str) and allergens.strip():
        allergens_str = allergens.strip()
    else:
        allergens_str = "None detected"

    additives = row.get("additives") or row.get("additives_tags")
    if isinstance(additives, (list, tuple)):
        additives_str = ", ".join(str(a).replace("en:", "").upper() for a in additives[:8])
    elif isinstance(additives, str) and additives.strip():
        additives_str = additives.strip()
    else:
        additives_str = "None"

    raw_nutri = row.get("nutriscore_grade")
    nutriscore = (
        str(raw_nutri).upper() if isinstance(raw_nutri, str) and raw_nutri.strip() else "N/A"
    )

    raw_nova = row.get("nova_group")
    if isinstance(raw_nova, (int, float)) and not math.isnan(raw_nova):
        nova = str(int(raw_nova))
    else:
        nova = "N/A"

    def _fmt_float(val: Any, unit: str = "g", decimals: int = 1) -> str:
        if isinstance(val, (int, float)) and not math.isnan(val):
            return f"{val:.{decimals}f}{unit}"
        return "N/A"

    energy_str = _fmt_float(row.get("energy_kcal"), unit=" kcal", decimals=0)
    fat_str = _fmt_float(row.get("fat_g"), unit="g", decimals=1)
    carbs_str = _fmt_float(row.get("carbs_g"), unit="g", decimals=1)
    protein_str = _fmt_float(row.get("protein_g"), unit="g", decimals=1)
    salt_str = _fmt_float(row.get("salt_g"), unit="g", decimals=2)

    card = (
        f"Product: {name_str} | Brand: {brand_str} | Categories: {categories_str} | "
        f"Ingredients: {ingredients_str} | Allergens: {allergens_str} | Additives: {additives_str} | "
        f"Nutri-Score: {nutriscore} | NOVA: {nova} | "
        f"Nutrition per 100g: Energy: {energy_str}, Fat: {fat_str}, Carbs: {carbs_str}, Protein: {protein_str}, Salt: {salt_str}"
    )
    return card
