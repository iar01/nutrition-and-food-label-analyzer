import operator
from typing import Annotated, Any, TypedDict

from langgraph.graph import END, START, StateGraph


def merge_dicts(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    return {**left, **right}


class State(TypedDict, total=False):
    text: str
    kind: str
    log: Annotated[list[str], operator.add]
    findings: Annotated[dict[str, Any], merge_dicts]


def classify(state: State) -> dict[str, Any]:
    kind = "barcode" if state["text"].isdigit() else "text"
    return {"kind": kind, "log": [f"classify -> {kind}"]}


def analyst_a(state: State) -> dict[str, Any]:
    return {"findings": {"a": "read the ingredients"}, "log": ["analyst_a done"]}


def analyst_b(state: State) -> dict[str, Any]:
    return {"findings": {"b": "read the additives"}, "log": ["analyst_b done"]}


def join(state: State) -> None:
    return None


def route(state: State) -> list[str] | str:
    return ["analyst_a", "analyst_b"] if state["kind"] == "text" else END


builder = StateGraph(State)  # type: ignore[type-var]
builder.add_node("classify", classify)
builder.add_node("analyst_a", analyst_a)
builder.add_node("analyst_b", analyst_b)
builder.add_node("join", join)
builder.add_edge(START, "classify")
builder.add_conditional_edges("classify", route)
builder.add_edge(["analyst_a", "analyst_b"], "join")
builder.add_edge("join", END)
graph = builder.compile()

for text in ["nutella", "3017620422003"]:
    out = graph.invoke({"text": text, "log": [], "findings": {}})
    print(text, "->", out["log"], out["findings"])

print(graph.get_graph().draw_mermaid())
