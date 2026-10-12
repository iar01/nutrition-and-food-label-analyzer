"""Deterministic three-valued logic rules for dietary profiles (yes / no / unknown)."""

# Standard allergen tags associated with specific dietary restrictions
GLUTEN_ALLERGENS = {
    "en:gluten",
    "en:wheat",
    "en:barley",
    "en:rye",
    "en:oats",
    "en:spelt",
    "en:kamut",
}

LACTOSE_ALLERGENS = {
    "en:milk",
    "en:lactose",
    "en:dairy",
}

NUT_ALLERGENS = {
    "en:nuts",
    "en:peanuts",
    "en:almonds",
    "en:hazelnuts",
    "en:walnuts",
    "en:cashews",
    "en:pecan-nuts",
    "en:brazil-nuts",
    "en:pistachio-nuts",
    "en:macadamia-nuts",
}

ANIMAL_DERIVED_ALLERGENS = {
    "en:milk",
    "en:eggs",
    "en:fish",
    "en:crustaceans",
    "en:molluscs",
}

NON_VEGETARIAN_ALLERGENS = {
    "en:fish",
    "en:crustaceans",
    "en:molluscs",
}


def derive_diet_flags(
    analysis_tags: list[str] | None,
    allergens: list[str] | None,
    traces: list[str] | None,
    labels: list[str] | None = None,
    palm_oil_count: int | None = None,
) -> dict[str, str]:
    """Derive dietary compliance flags using strict three-valued logic.

    Values:
    - 'yes': Verified safe through verified tags, labels, or ingredient analysis.
    - 'no': Explicitly contains incompatible ingredients, allergens, or traces.
    - 'unknown': Insufficient or unverified data. NEVER default to 'yes'.
    """
    analysis = set(analysis_tags or [])
    all_allergens = set(allergens or []) | set(traces or [])
    labels_set = set(labels or [])

    flags: dict[str, str] = {}

    # 1. Vegan Flag
    if "en:non-vegan" in analysis or any(a in all_allergens for a in ANIMAL_DERIVED_ALLERGENS):
        flags["vegan"] = "no"
    elif "en:vegan" in analysis or "en:vegan" in labels_set:
        flags["vegan"] = "yes"
    else:
        flags["vegan"] = "unknown"

    # 2. Vegetarian Flag
    if "en:non-vegetarian" in analysis or any(a in all_allergens for a in NON_VEGETARIAN_ALLERGENS):
        flags["vegetarian"] = "no"
    elif "en:vegetarian" in analysis or "en:vegetarian" in labels_set or flags["vegan"] == "yes":
        flags["vegetarian"] = "yes"
    else:
        flags["vegetarian"] = "unknown"

    # 3. Palm Oil Free Flag
    if "en:palm-oil" in analysis or (palm_oil_count is not None and palm_oil_count > 0):
        flags["palm_oil_free"] = "no"
    elif "en:palm-oil-free" in analysis or "en:palm-oil-free" in labels_set:
        flags["palm_oil_free"] = "yes"
    else:
        flags["palm_oil_free"] = "unknown"

    # 4. Gluten Free Flag
    if any(a in all_allergens for a in GLUTEN_ALLERGENS):
        flags["gluten_free"] = "no"
    elif "en:gluten-free" in labels_set or "en:sans-gluten" in labels_set:
        flags["gluten_free"] = "yes"
    else:
        flags["gluten_free"] = "unknown"

    # 5. Lactose Free Flag
    if any(a in all_allergens for a in LACTOSE_ALLERGENS):
        flags["lactose_free"] = "no"
    elif "en:lactose-free" in labels_set or flags["vegan"] == "yes":
        flags["lactose_free"] = "yes"
    else:
        flags["lactose_free"] = "unknown"

    # 6. Nut Free Flag
    if any(a in all_allergens for a in NUT_ALLERGENS):
        flags["nut_free"] = "no"
    elif "en:nut-free" in labels_set or "en:peanut-free" in labels_set:
        flags["nut_free"] = "yes"
    else:
        flags["nut_free"] = "unknown"

    return flags
