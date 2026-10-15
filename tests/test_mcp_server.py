import asyncio
from typing import Any, get_args

import pytest
from fastmcp import Client
from fastmcp.exceptions import ToolError
from labellens.agents.deps import Deps
from labellens.agents.rules import ALLERGEN_TAG, DIET_FLAG
from labellens.mcp_server import server as server_module
from labellens.mcp_server.server import create_server

PRODUCT: dict[str, Any] = {
    "code": "12345678",
    "name": "Test Spread",
    "brand": "Acme",
    "ingredients": "sugar, palm oil, hazelnuts, skimmed milk powder, emulsifier (lecithin)",
    "allergens_tags": ["en:milk", "en:nuts"],
    "traces_tags": [],
    "additives_tags": ["en:e322"],
    "diet_vegan": "no",
    "diet_vegetarian": "yes",
    "nutriscore_grade": "e",
    "nova_group": 4.0,
    "sugars_g": 56.0,
    "salt_g": 0.1,
    "sat_fat_g": 10.0,
    "fat_g": 30.0,
    "categories_tags": ["en:spreads"],
}
CARDS = {
    "e322": {
        "key": "e322",
        "e_number": "E322",
        "title": "E322 Lecithins",
        "text": "An emulsifier.",
        "vegan": "varies",
        "source_url": "",
    },
}


class FakeRepo:
    def get(self, code: str) -> dict[str, Any] | None:
        return PRODUCT if code in ("12345678", "0000012345678") else None


class FakeSearcher:
    def products(self, query: str, limit: int = 5, filters: Any = None) -> list[dict[str, Any]]:
        return [
            {
                "code": "12345678",
                "name": "Test Spread",
                "brands": "Acme",
                "nutriscore": "e",
                "score": 0.9,
            }
        ]

    def knowledge(self, query: str, k: int = 3, exclude_types: Any = ()) -> list[dict[str, Any]]:
        return [
            {
                "key": "diet-vegan",
                "type": "diet_rule",
                "title": "What vegan means",
                "text": "...",
                "source_url": "",
            }
        ]


def make_server() -> Any:
    deps = Deps(llm=None, repo=FakeRepo(), searcher=FakeSearcher(), additive_cards=CARDS)
    return create_server(lambda: deps)


def call(name: str, args: dict[str, Any]) -> dict[str, Any]:
    async def run() -> dict[str, Any]:
        async with Client(make_server()) as client:
            result = await client.call_tool(name, args)
            return dict(result.structured_content or {})

    return asyncio.run(run())


def tool_names() -> set[str]:
    async def run() -> set[str]:
        async with Client(make_server()) as client:
            return {t.name for t in await client.list_tools()}

    return asyncio.run(run())


def test_all_expected_tools_are_listed() -> None:
    assert tool_names() >= {
        "lookup_by_barcode",
        "search_products",
        "search_knowledge",
        "get_nutrition",
        "explain_additive",
        "check_diet_fit",
        "find_alternatives",
        "compare_products",
    }


def test_lookup_found_and_not_found() -> None:
    assert call("lookup_by_barcode", {"code": "12345678"})["product"]["name"] == "Test Spread"
    out = call("lookup_by_barcode", {"code": "99999999"})
    assert out["found"] is False and out["error"] == "not_found"


def test_invalid_barcode_is_rejected_by_the_schema() -> None:
    with pytest.raises(ToolError):
        call("lookup_by_barcode", {"code": "abc"})


def test_unknown_diet_value_is_rejected() -> None:
    with pytest.raises(ToolError):
        call("check_diet_fit", {"code": "12345678", "diets": ["keto"]})


def test_check_diet_fit_reports_contains_and_not_suitable() -> None:
    out = call("check_diet_fit", {"code": "12345678", "diets": ["vegan"], "allergens": ["milk"]})
    assert out["verdicts"]["allergens"]["milk"]["status"] == "contains"
    assert out["verdicts"]["diets"]["vegan"]["status"] == "not_suitable"
    assert out["verdicts"]["overall"] == "not_suitable"


def test_explain_additive_by_e_number_by_name_and_miss() -> None:
    assert call("explain_additive", {"identifier": "E322"})["card"]["vegan"] == "varies"
    assert call("explain_additive", {"identifier": "lecithins"})["found"] is True
    miss = call("explain_additive", {"identifier": "unobtainium"})
    assert miss["found"] is False and "suggestions" in miss


def test_compare_needs_at_least_two_barcodes() -> None:
    with pytest.raises(ToolError):
        call("compare_products", {"codes": ["12345678"]})
    out = call("compare_products", {"codes": ["12345678", "99999999"]})
    assert out["missing"] == ["99999999"] and out["best_nutriscore_code"] == "12345678"


def test_literal_lists_match_the_rules_tables() -> None:
    assert set(get_args(server_module.Diet)) == set(DIET_FLAG)
    assert set(get_args(server_module.Allergen)) == set(ALLERGEN_TAG)
