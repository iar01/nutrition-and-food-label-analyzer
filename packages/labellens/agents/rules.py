from typing import Any

DIET_FLAG: dict[str, str] = {
    "vegan": "diet_vegan",
    "vegetarian": "diet_vegetarian",
    "gluten_free": "diet_gluten_free",
    "lactose_free": "diet_lactose_free",
    "palm_oil_free": "diet_palm_oil_free",
    "nut_free": "diet_nut_free",
}

ALLERGEN_TAG: dict[str, str] = {
    "milk": "en:milk",
    "eggs": "en:eggs",
    "peanuts": "en:peanuts",
    "nuts": "en:nuts",
    "soy": "en:soybeans",
    "gluten": "en:gluten",
    "fish": "en:fish",
    "crustaceans": "en:crustaceans",
    "molluscs": "en:molluscs",
    "sesame": "en:sesame-seeds",
    "celery": "en:celery",
    "mustard": "en:mustard",
    "lupin": "en:lupin",
    "sulphites": "en:sulphur-dioxide-and-sulphites",
}

# Additives whose source can matter for an allergy (key is the card key).
ALLERGEN_ADDITIVE_HINTS: dict[str, set[str]] = {"soy": {"e322"}}

# UK FSA traffic-light thresholds per 100 g for solid foods: (low_max, high_min).
FSA_PER_100G: dict[str, tuple[float, float]] = {
    "sugars_g": (5.0, 22.5),
    "salt_g": (0.3, 1.5),
    "sat_fat_g": (1.5, 5.0),
    "fat_g": (3.0, 17.5),
}
GOAL_NUTRIENT: dict[str, str] = {
    "low_sugar": "sugars_g",
    "low_salt": "salt_g",
    "low_sat_fat": "sat_fat_g",
}

Result = dict[str, Any]


def additive_keys(product: dict[str, Any]) -> list[str]:
    """['en:e471', 'en:e322'] -> ['e471', 'e322']"""
    return [t.split(":", 1)[-1].lower() for t in (product.get("additives_tags") or [])]


def diet_verdict(product: dict[str, Any], diet: str, cards: dict[str, dict[str, Any]]) -> Result:
    if not product.get("ingredients"):
        return {
            "status": "unknown",
            "reasons": ["The ingredient list is missing in the data."],
            "evidence_ids": [],
        }

    flag = product.get(DIET_FLAG[diet]) or "unknown"
    status = {"yes": "suitable", "no": "not_suitable"}.get(flag, "unknown")
    reasons: list[str] = []
    evidence_ids: list[str] = []

    if status == "suitable":
        reasons.append("The product data marks it as suitable.")
    elif status == "not_suitable":
        reasons.append("The product data marks it as not suitable.")
    else:
        reasons.append("The product data does not settle this.")

    if diet == "vegan":
        for key in additive_keys(product):
            card = cards.get(key)
            if card is None:
                continue
            origin = card.get("vegan")
            if origin == "no":
                status = "not_suitable"
                reasons.append(f"{card['e_number']} ({card['title']}) is animal-derived.")
                evidence_ids.append(f"kb:{key}")
            elif origin == "varies" and status == "suitable":
                status = "unknown"
                reasons.append(f"The source of {card['e_number']} is not stated (plant or animal).")
                evidence_ids.append(f"kb:{key}")

    return {"status": status, "reasons": reasons, "evidence_ids": evidence_ids}


def allergen_status(
    product: dict[str, Any], allergen: str, cards: dict[str, dict[str, Any]]
) -> Result:
    tag = ALLERGEN_TAG[allergen]
    allergens = product.get("allergens_tags")
    traces = product.get("traces_tags") or []

    if allergens is None or not product.get("ingredients"):
        return {"status": "unknown", "reasons": ["Allergen data is missing."], "evidence_ids": []}
    if tag in allergens:
        return {
            "status": "contains",
            "reasons": [f"Declared allergen: {allergen}."],
            "evidence_ids": [],
        }
    if tag in traces:
        return {
            "status": "may_contain",
            "reasons": [f"May contain traces of {allergen}."],
            "evidence_ids": [],
        }

    hints = ALLERGEN_ADDITIVE_HINTS.get(allergen, set())
    present = [k for k in additive_keys(product) if k in hints]
    if present:
        key = present[0]
        card = cards.get(key, {})
        return {
            "status": "unknown",
            "reasons": [
                f"{card.get('e_number', key.upper())} can be made from {allergen}; the label does not say."
            ],
            "evidence_ids": [f"kb:{key}"] if key in cards else [],
        }
    return {
        "status": "not_listed",
        "reasons": [f"{allergen} is not listed in the data."],
        "evidence_ids": [],
    }


def nutrition_levels(product: dict[str, Any]) -> dict[str, Result]:
    out: dict[str, Result] = {}
    for nutrient, (low_max, high_min) in FSA_PER_100G.items():
        value = product.get(nutrient)
        if value is None:
            level = "unknown"
        elif value <= low_max:
            level = "low"
        elif value > high_min:
            level = "high"
        else:
            level = "medium"
        out[nutrient] = {"value": value, "level": level}
    return out


def goal_checks(nutrition: dict[str, Result], goals: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for goal in goals:
        nutrient = GOAL_NUTRIENT.get(goal)
        if nutrient is None:
            continue
        level = nutrition[nutrient]["level"]
        out[goal] = {"low": "meets", "high": "exceeds", "medium": "partly", "unknown": "unknown"}[
            level
        ]
    return out


def overall_status(diets: dict[str, Result], allergens: dict[str, Result]) -> str:
    if not diets and not allergens:
        return "no_profile"
    if any(r["status"] == "contains" for r in allergens.values()):
        return "not_suitable"
    if any(r["status"] == "not_suitable" for r in diets.values()):
        return "not_suitable"
    if any(
        r["status"] in ("unknown", "may_contain") for r in [*diets.values(), *allergens.values()]
    ):
        return "check"
    return "no_conflicts_found"


def compute_verdicts(
    product: dict[str, Any], profile: dict[str, Any], cards: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    diets = {d: diet_verdict(product, d, cards) for d in profile.get("diets", []) if d in DIET_FLAG}
    allergens = {
        a: allergen_status(product, a, cards)
        for a in profile.get("allergens", [])
        if a in ALLERGEN_TAG
    }
    nutrition = nutrition_levels(product)
    goals = goal_checks(nutrition, profile.get("goals", []))
    return {
        "diets": diets,
        "allergens": allergens,
        "nutrition": nutrition,
        "goals": goals,
        "overall": overall_status(diets, allergens),
    }
