from typing import Any

from labellens.agents.deps import Deps
from labellens.agents.evidence import product_evidence
from labellens.agents.rules import compute_verdicts
from labellens.agents.state import AgentState

LETTERS = "abcde"
MAX_ALTERNATIVES = 3


def alternatives_node(state: AgentState, deps: Deps) -> dict[str, Any]:
    product = state["product"] or {}
    profile = state.get("profile", {})
    grade = (product.get("nutriscore_grade") or "").lower()
    if grade not in LETTERS or grade == "a":
        return {"alternatives": []}

    better = list(LETTERS[: LETTERS.index(grade)])
    accepted: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    categories = product.get("categories_tags") or []

    for category in reversed(categories[-3:]):  # most specific category first
        filters = {
            "category": category,
            "nutriscore_in": better,
            "diets": profile.get("diets", []),
            "exclude_allergens": profile.get("allergens", []),
        }
        for hit in deps.searcher.products(product.get("name") or "", limit=10, filters=filters):
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
