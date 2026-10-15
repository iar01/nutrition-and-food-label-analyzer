import json
import logging
import re
from typing import Any

from labellens.agents.deps import Deps
from labellens.agents.evidence import card_evidence, kb_hit_evidence
from labellens.agents.prompts import ADDITIVE_SYSTEM, INGREDIENT_SYSTEM
from labellens.agents.rules import additive_keys, compute_verdicts
from labellens.agents.schemas import AdditiveFindings, IngredientFindings
from labellens.agents.state import AgentState
from labellens.llm.structured import structured_call

logger = logging.getLogger(__name__)
SUGAR_WORDS = (
    "sugar",
    "glucose",
    "fructose",
    "dextrose",
    "maltose",
    "syrup",
    "honey",
    "maltodextrin",
    "sucrose",
)
MAX_ADDITIVES = 8


def ingredient_markers(text: str) -> dict[str, Any]:
    items = [i.strip() for i in re.split(r",(?![^()]*\))", text) if i.strip()]
    lowered = text.lower()
    return {
        "count": len(items),
        "first_three": items[:3],
        "sugar_terms": sorted({w for w in SUGAR_WORDS if w in lowered}),
        "mentions_palm": "palm" in lowered,
    }


def ingredient_analyst(state: AgentState, deps: Deps) -> dict[str, Any]:
    product = state["product"] or {}
    profile = state.get("profile", {})
    text = product.get("ingredients") or ""
    if not text:
        return {
            "findings": {
                "ingredients": {
                    "summary": "The ingredient list is missing in the data.",
                    "notable": [],
                }
            }
        }

    markers = ingredient_markers(text)
    query = f"{' '.join(profile.get('diets', []))} {text[:200]}".strip()
    hits = deps.searcher.knowledge(query, k=3, exclude_types=["additive"])
    evidence = [kb_hit_evidence(h) for h in hits]
    allowed = {e["id"] for e in evidence}

    payload = {
        "ingredients": text[:600],
        "markers": markers,
        "profile": profile,
        "evidence": [{"id": e["id"], "title": e["title"], "text": e["text"]} for e in evidence],
    }
    try:
        result = structured_call(
            deps.llm, IngredientFindings, INGREDIENT_SYSTEM, json.dumps(payload)
        )
        for note in result.notable:
            note.evidence_ids = [i for i in note.evidence_ids if i in allowed]  # drop invented ids
        out = result.model_dump()
    except Exception:
        logger.warning("ingredient_analyst fell back to a template", exc_info=True)
        out = {
            "summary": f"{markers['count']} ingredients. The first ones are: {', '.join(markers['first_three'])}.",
            "notable": [],
        }
    return {"findings": {"ingredients": out}, "evidence": evidence}


def additive_analyst(state: AgentState, deps: Deps) -> dict[str, Any]:
    product = state["product"] or {}
    profile = state.get("profile", {})
    keys = additive_keys(product)[:MAX_ADDITIVES]
    cards = [deps.additive_cards[k] for k in keys if k in deps.additive_cards]
    missing = [k.upper() for k in keys if k not in deps.additive_cards]
    if not cards:
        return {"findings": {"additives": {"notes": [], "missing": missing}}}

    evidence = [card_evidence(c) for c in cards]
    payload = {
        "profile": profile,
        "cards": [{"id": e["id"], "title": e["title"], "text": e["text"]} for e in evidence],
    }
    try:
        result = structured_call(deps.llm, AdditiveFindings, ADDITIVE_SYSTEM, json.dumps(payload))
        notes = [
            n.model_dump() for n in result.notes if n.evidence_id in {e["id"] for e in evidence}
        ]
    except Exception:
        logger.warning("additive_analyst fell back to card text", exc_info=True)
        notes = [
            {
                "e_number": c["e_number"],
                "explanation": c["text"],
                "relevant_to_user": None,
                "evidence_id": f"kb:{c['key']}",
            }
            for c in cards
        ]
    return {"findings": {"additives": {"notes": notes, "missing": missing}}, "evidence": evidence}


def diet_checker(state: AgentState, deps: Deps) -> dict[str, Any]:
    verdicts = compute_verdicts(
        state["product"] or {}, state.get("profile", {}), deps.additive_cards
    )
    ids = {
        i
        for section in ("diets", "allergens")
        for r in verdicts[section].values()
        for i in r["evidence_ids"]
    }
    evidence = [
        card_evidence(deps.additive_cards[i.split(":", 1)[1]])
        for i in sorted(ids)
        if i.split(":", 1)[1] in deps.additive_cards
    ]
    return {"verdicts": verdicts, "evidence": evidence}
