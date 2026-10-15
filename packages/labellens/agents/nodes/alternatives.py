from typing import Any

from labellens.agents.deps import Deps
from labellens.agents.evidence import product_evidence
from labellens.agents.rules import ALLERGEN_TAG, DIET_FLAG, compute_verdicts
from labellens.agents.state import AgentState
from qdrant_client import models

LETTERS = "abcde"
MAX_ALTERNATIVES = 3


def alternatives_node(state: AgentState, deps: Deps) -> dict[str, Any]:
    product = state["product"] or {}
    profile = state.get("profile", {})
    grade = (product.get("nutriscore_grade") or "").lower()
    if grade not in LETTERS or grade == "a":
        return {"alternatives": []}

    better = list(LETTERS[: LETTERS.index(grade)])
    must: list[models.Condition] = [
        models.FieldCondition(key="nutriscore", match=models.MatchAny(any=better))
    ]
    for diet in profile.get("diets", []):
        if diet in DIET_FLAG:
            must.append(
                models.FieldCondition(key=DIET_FLAG[diet], match=models.MatchValue(value="yes"))
            )
    avoid = [ALLERGEN_TAG[a] for a in profile.get("allergens", []) if a in ALLERGEN_TAG]
    must_not: list[models.Condition] | None = (
        [models.FieldCondition(key="allergens", match=models.MatchAny(any=avoid))]
        if avoid
        else None
    )

    accepted: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    categories = product.get("categories_tags") or []
    for category in reversed(categories[-3:]):  # most specific category first
        query_filter = models.Filter(
            must=[
                *must,
                models.FieldCondition(key="categories", match=models.MatchValue(value=category)),
            ],
            must_not=must_not,
        )
        for hit in deps.searcher.products(
            product.get("name") or "", limit=10, query_filter=query_filter
        ):
            if hit["code"] == product["code"] or any(a["code"] == hit["code"] for a in accepted):
                continue
            full = deps.repo.get(hit["code"])
            if full is None:
                continue
            verdicts = compute_verdicts(
                full, profile, deps.additive_cards
            )  # second, independent check
            if verdicts["overall"] not in ("no_conflicts_found", "no_profile"):
                continue
            accepted.append(
                {
                    "code": full["code"],
                    "name": full.get("name"),
                    "brand": full.get("brand"),
                    "nutriscore": full.get("nutriscore_grade"),
                }
            )
            evidence.append(product_evidence(full))
            if len(accepted) >= MAX_ALTERNATIVES:
                return {"alternatives": accepted, "evidence": evidence}
    return {"alternatives": accepted, "evidence": evidence}
