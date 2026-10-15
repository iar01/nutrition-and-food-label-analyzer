import re
from typing import Any

from labellens.agents.deps import Deps
from labellens.agents.prompts import ROUTER_SYSTEM
from labellens.agents.schemas import RouterDecision
from labellens.agents.state import AgentState
from labellens.llm.structured import structured_call

BARCODE_RE = re.compile(r"\b\d{8,14}\b")
ALT_RE = re.compile(
    r"\b(alternatives?|healthier|better option|better choice|instead|swap)\b", re.IGNORECASE
)


def router(state: AgentState, deps: Deps) -> dict[str, Any]:
    text = state.get("user_text", "").strip()
    wants_alternatives = bool(ALT_RE.search(text))

    match = BARCODE_RE.search(text)
    if match:  # no LLM needed
        return {
            "input_kind": "barcode",
            "product_query": match.group(0),
            "wants_alternatives": wants_alternatives,
        }

    try:
        decision = structured_call(deps.llm, RouterDecision, ROUTER_SYSTEM, text)
    except Exception:  # LLM down or confused: fall back to searching with the raw text
        return {
            "input_kind": "text",
            "product_query": text,
            "wants_alternatives": wants_alternatives,
        }

    query = decision.product_query or text
    if not query:
        return {
            "error": "no_query",
            "answer": "Tell me a product name or a barcode and I will check it for you.",
        }
    return {
        "input_kind": "text",
        "product_query": query,
        "wants_alternatives": wants_alternatives or decision.wants_alternatives,
    }
