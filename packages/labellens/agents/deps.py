from dataclasses import dataclass, field
from typing import Any

from labellens.cache import PromptCache
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
    prompt_cache: PromptCache = field(default_factory=PromptCache)


def build_default_deps() -> Deps:
    return Deps(
        llm=get_llm(),
        repo=ProductRepo(),
        searcher=Searcher(),
        additive_cards=load_additive_cards(),
        prompt_cache=PromptCache(),
    )
