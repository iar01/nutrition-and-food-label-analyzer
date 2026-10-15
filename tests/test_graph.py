from typing import Any

from labellens.agents.deps import Deps
from labellens.agents.graph import build_graph
from labellens.llm.fake import FakeLLM
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

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
        "title": "Lecithins",
        "text": "An emulsifier.",
        "vegan": "varies",
        "source_url": "",
    }
}


class FakeRepo:
    def get(self, code: str) -> dict[str, Any] | None:
        return PRODUCT if code == "12345678" else None


class FakeSearcher:
    def __init__(self, n: int = 1) -> None:
        self.n = n

    def products(
        self, query: str, limit: int = 5, query_filter: Any = None
    ) -> list[dict[str, Any]]:
        hit = {
            "code": "12345678",
            "name": "Test Spread",
            "brands": "Acme",
            "nutriscore": "e",
            "score": 0.9,
        }
        return [hit] * self.n

    def knowledge(self, query: str, k: int = 3, exclude_types: Any = ()) -> list[dict[str, Any]]:
        return []


def make_deps(n_candidates: int = 1) -> Deps:
    return Deps(
        llm=FakeLLM(), repo=FakeRepo(), searcher=FakeSearcher(n_candidates), additive_cards=CARDS
    )


def initial(text: str, **extra: Any) -> dict[str, Any]:
    return {
        "user_text": text,
        "messages": [HumanMessage(content=text)],
        "profile": {"diets": ["vegan"], "allergens": ["milk"]},
        "evidence": [],
        "findings": {},
        "revisions": 0,
        "error": None,
        "critic_feedback": None,
        **extra,
    }


def test_barcode_flow_produces_correct_verdicts() -> Any:
    out = build_graph(make_deps()).invoke(initial("check 12345678"))
    assert out["verdicts"]["allergens"]["milk"]["status"] == "contains"
    assert out["verdicts"]["diets"]["vegan"]["status"] == "not_suitable"
    assert out["verdicts"]["overall"] == "not_suitable"
    assert "Sources" in out["answer"]


def test_unknown_barcode_gives_helpful_message() -> Any:
    out = build_graph(make_deps()).invoke(initial("check 99999999"))
    assert out["error"] == "not_found"
    assert "could not find" in out["answer"]


def test_text_flow_interrupts_and_resumes() -> Any:
    graph = build_graph(make_deps(n_candidates=2), InMemorySaver())
    config = {"configurable": {"thread_id": "t1"}}
    first = graph.invoke(initial("nutella"), config)
    assert "__interrupt__" in first
    final = graph.invoke(Command(resume={"code": "12345678"}), config)
    assert final["product"]["code"] == "12345678"
    assert final["verdicts"]["overall"] == "not_suitable"
