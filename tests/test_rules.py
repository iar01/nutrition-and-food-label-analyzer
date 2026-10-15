from typing import Any

from labellens.agents.rules import allergen_status, compute_verdicts, diet_verdict

CARDS = {
    "e120": {"e_number": "E120", "title": "Carmine", "vegan": "no"},
    "e471": {"e_number": "E471", "title": "Mono- and diglycerides", "vegan": "varies"},
    "e322": {"e_number": "E322", "title": "Lecithins", "vegan": "varies"},
}


def product(**overrides: Any) -> dict[str, Any]:
    base = {
        "code": "1",
        "ingredients": "sugar, milk powder",
        "allergens_tags": ["en:milk"],
        "traces_tags": ["en:nuts"],
        "additives_tags": [],
        "diet_vegan": "no",
        "diet_vegetarian": "yes",
        "sugars_g": 30.0,
        "salt_g": 0.1,
        "sat_fat_g": 2.0,
        "fat_g": 10.0,
    }
    base.update(overrides)
    return base


def test_declared_allergen_is_contains() -> Any:
    assert allergen_status(product(), "milk", CARDS)["status"] == "contains"


def test_trace_allergen_is_may_contain() -> Any:
    assert allergen_status(product(), "nuts", CARDS)["status"] == "may_contain"


def test_missing_allergen_data_is_unknown_not_safe() -> Any:
    assert allergen_status(product(allergens_tags=None), "milk", CARDS)["status"] == "unknown"


def test_soy_lecithin_hint_makes_soy_unknown() -> Any:
    p = product(allergens_tags=[], traces_tags=[], additives_tags=["en:e322"])
    assert allergen_status(p, "soy", CARDS)["status"] == "unknown"


def test_vegan_flag_yes_but_carmine_wins() -> Any:
    p = product(diet_vegan="yes", additives_tags=["en:e120"])
    assert diet_verdict(p, "vegan", CARDS)["status"] == "not_suitable"


def test_vegan_flag_yes_but_unknown_source_additive_downgrades() -> Any:
    p = product(diet_vegan="yes", additives_tags=["en:e471"])
    assert diet_verdict(p, "vegan", CARDS)["status"] == "unknown"


def test_missing_ingredients_make_every_diet_unknown() -> Any:
    p = product(ingredients=None, diet_vegetarian="yes")
    assert diet_verdict(p, "vegetarian", CARDS)["status"] == "unknown"


def test_overall_not_suitable_when_allergen_present() -> Any:
    v = compute_verdicts(product(), {"diets": ["vegetarian"], "allergens": ["milk"]}, CARDS)
    assert v["overall"] == "not_suitable"


def test_overall_no_profile_when_nothing_to_check() -> Any:
    assert compute_verdicts(product(), {}, CARDS)["overall"] == "no_profile"


def test_nutrition_levels() -> Any:
    v = compute_verdicts(product(), {"goals": ["low_sugar"]}, CARDS)
    assert v["nutrition"]["sugars_g"]["level"] == "high"
    assert v["goals"]["low_sugar"] == "exceeds"
