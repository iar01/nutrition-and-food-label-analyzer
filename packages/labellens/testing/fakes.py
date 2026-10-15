from pathlib import Path
from typing import Any

import numpy as np
from langgraph.checkpoint.memory import InMemorySaver

from labellens.agents.deps import Deps
from labellens.agents.graph import build_graph
from labellens.api.services import FeedbackStore, ReadyCheck, Services
from labellens.llm.fake import FakeLLM

PRODUCT: dict[str, Any] = {
    "code": "12345678",
    "name": "Test Spread",
    "brand": "Acme",
    "quantity": "400 g",
    "ingredients": "sugar, palm oil, hazelnuts, skimmed milk powder, emulsifier (lecithin)",
    "allergens_tags": ["en:milk", "en:nuts"],
    "traces_tags": [],
    "additives_tags": ["en:e322"],
    "diet_vegan": "no",
    "diet_vegetarian": "yes",
    "nutriscore_grade": "e",
    "nova_group": 4.0,
    "energy_kcal": 540.0,
    "sugars_g": 56.0,
    "salt_g": 0.1,
    "sat_fat_g": 10.0,
    "fat_g": 30.0,
    "categories_tags": ["en:spreads"],
}
CARDS: dict[str, dict[str, Any]] = {
    "e322": {
        "key": "e322",
        "e_number": "E322",
        "title": "E322 Lecithins",
        "text": "An emulsifier.",
        "vegan": "varies",
        "source_url": "",
    },
}
HIT: dict[str, Any] = {
    "code": "12345678",
    "name": "Test Spread",
    "brands": "Acme",
    "nutriscore": "e",
    "score": 0.9,
}


class FakeRepo:
    def get(self, code: str) -> dict[str, Any] | None:
        return PRODUCT if code in ("12345678", "0000012345678") else None

    def ping(self) -> bool:
        return True


class FakeSearcher:
    def __init__(self, n_candidates: int = 1) -> None:
        self.n = n_candidates

    def products(self, query: str, limit: int = 5, filters: Any = None) -> list[dict[str, Any]]:
        return [dict(HIT) for _ in range(self.n)]

    def knowledge(self, query: str, k: int = 3, exclude_types: Any = ()) -> list[dict[str, Any]]:
        return []

    def by_image(self, vector: Any, limit: int = 5) -> list[dict[str, Any]]:
        return [dict(HIT)]


class FakeClip:
    def embed_images(self, images: list[Any]) -> np.ndarray:
        return np.zeros((len(images), 512))


def make_fake_deps(n_candidates: int = 1) -> Deps:
    return Deps(
        llm=FakeLLM(), repo=FakeRepo(), searcher=FakeSearcher(n_candidates), additive_cards=CARDS
    )


def make_fake_services(feedback_path: Path, n_candidates: int = 1) -> Services:
    deps = make_fake_deps(n_candidates)
    return Services(
        deps=deps,
        graph=build_graph(deps, InMemorySaver()),
        feedback=FeedbackStore(feedback_path),
        get_product=deps.repo.get,
        get_clip=lambda: FakeClip(),
        checks=[
            ReadyCheck("database", lambda: True, critical=True),
            ReadyCheck("qdrant", lambda: True, critical=True),
            ReadyCheck("llm", lambda: True, critical=False),
        ],
    )
