import operator
from typing import Annotated, Any, TypedDict

from langchain_core.messages import AnyMessage
from langgraph.graph.message import add_messages


def merge_dicts(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    return {**left, **right}


class AgentState(TypedDict, total=False):
    messages: Annotated[list[AnyMessage], add_messages]
    user_text: str
    profile: dict[str, Any]  # {'diets': [...], 'allergens': [...], 'goals': [...]}
    auto_pick: bool  # skip the "which product?" question
    input_kind: str
    product_query: str | None
    wants_alternatives: bool
    candidates: list[dict[str, Any]]
    product: dict[str, Any] | None
    evidence: Annotated[list[dict[str, Any]], operator.add]
    findings: Annotated[dict[str, Any], merge_dicts]
    verdicts: dict[str, Any]
    alternatives: list[dict[str, Any]]
    draft: dict[str, Any]
    critic_feedback: str | None
    revisions: int
    answer: str | None
    error: str | None
