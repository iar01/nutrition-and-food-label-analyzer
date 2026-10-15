from collections.abc import Callable
from typing import Any

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph

from labellens.agents.deps import Deps
from labellens.agents.nodes.alternatives import alternatives_node
from labellens.agents.nodes.analysts import additive_analyst, diet_checker, ingredient_analyst
from labellens.agents.nodes.candidates import choose_product, find_candidates
from labellens.agents.nodes.finish import critic, synthesizer
from labellens.agents.nodes.router import router
from labellens.agents.state import AgentState

ANALYSTS = ["ingredient_analyst", "additive_analyst", "diet_checker"]
NodeFn = Callable[[AgentState, Deps], dict[str, Any]]


def bind(fn: NodeFn, deps: Deps) -> Callable[[AgentState], dict[str, Any]]:
    """Turn a node that needs (state, deps) into one that only needs (state)."""

    def node(state: AgentState) -> dict[str, Any]:
        return fn(state, deps)

    return node


def join(state: AgentState) -> None:
    return None


def after_router(state: AgentState) -> str:
    return END if state.get("error") else "find_candidates"


def after_choose(state: AgentState) -> list[str] | str:
    if state.get("error") or not state.get("product"):
        return END
    return ANALYSTS  # a list means: run these in parallel


def after_join(state: AgentState) -> str:
    return "alternatives" if state.get("wants_alternatives") else "synthesizer"


def after_critic(state: AgentState) -> str:
    return "synthesizer" if state.get("critic_feedback") else END


def build_graph(deps: Deps, checkpointer: BaseCheckpointSaver | None = None) -> Any:
    b = StateGraph(AgentState)  # type: ignore
    b.add_node("router", bind(router, deps))  # type: ignore
    b.add_node("find_candidates", bind(find_candidates, deps))  # type: ignore
    b.add_node("choose_product", bind(choose_product, deps))  # type: ignore
    b.add_node("ingredient_analyst", bind(ingredient_analyst, deps))  # type: ignore
    b.add_node("additive_analyst", bind(additive_analyst, deps))  # type: ignore
    b.add_node("diet_checker", bind(diet_checker, deps))  # type: ignore
    b.add_node("join", join)
    b.add_node("alternatives", bind(alternatives_node, deps))  # type: ignore
    b.add_node("synthesizer", bind(synthesizer, deps))  # type: ignore
    b.add_node("critic", bind(critic, deps))  # type: ignore

    b.add_edge(START, "router")
    b.add_conditional_edges("router", after_router)
    b.add_edge("find_candidates", "choose_product")
    b.add_conditional_edges("choose_product", after_choose)
    b.add_edge(ANALYSTS, "join")
    b.add_conditional_edges("join", after_join)
    b.add_edge("alternatives", "synthesizer")
    b.add_edge("synthesizer", "critic")
    b.add_conditional_edges("critic", after_critic)
    return b.compile(checkpointer=checkpointer)
