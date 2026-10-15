from dataclasses import dataclass
from typing import Any

from labellens.llm.client import get_llm
from labellens.retrieval.search import Searcher
from labellens.tools.knowledge import load_additive_cards
from labellens.tools.products import ProductRepo


@dataclass
class Deps:
    llm: Any
    repo: Any
    searcher: Any
    additive_cards: dict[str, dict[str, Any]]


def build_default_deps() -> Deps:
    return Deps(
        llm=get_llm(),
        repo=ProductRepo(),
        searcher=Searcher(),
        additive_cards=load_additive_cards(),
    )
