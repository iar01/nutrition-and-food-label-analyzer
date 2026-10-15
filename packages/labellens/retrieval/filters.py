from typing import Any

from qdrant_client import models

from labellens.agents.rules import ALLERGEN_TAG, DIET_FLAG


def build_filter(filters: dict[str, Any] | None) -> models.Filter | None:
    """Turn a plain dictionary into a Qdrant filter.

    Keys: category (str), nutriscore_in (list of a-e), diets (list), exclude_allergens (list).
    """
    if not filters:
        return None

    must: list[models.Condition] = []
    must_not: list[models.Condition] = []

    if filters.get("category"):
        must.append(
            models.FieldCondition(
                key="categories", match=models.MatchValue(value=filters["category"])
            )
        )
    if filters.get("nutriscore_in"):
        grades = [str(g).lower() for g in filters["nutriscore_in"]]
        must.append(models.FieldCondition(key="nutriscore", match=models.MatchAny(any=grades)))
    for diet in filters.get("diets") or []:
        if diet in DIET_FLAG:
            must.append(
                models.FieldCondition(key=DIET_FLAG[diet], match=models.MatchValue(value="yes"))
            )
    avoid = [ALLERGEN_TAG[a] for a in filters.get("exclude_allergens") or [] if a in ALLERGEN_TAG]
    if avoid:
        must_not.append(models.FieldCondition(key="allergens", match=models.MatchAny(any=avoid)))

    if not must and not must_not:
        return None
    return models.Filter(must=must or None, must_not=must_not or None)
