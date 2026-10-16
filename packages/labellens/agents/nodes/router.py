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
    active_product = state.get("product")

    # Follow-up in an ongoing thread with an already loaded product
    if active_product:
        # Check if user entered a new barcode to switch products
        match = BARCODE_RE.search(text)
        if match:
            return {
                "input_kind": "barcode",
                "product_query": match.group(0),
                "wants_alternatives": wants_alternatives,
                "product": None,
                "candidates": [],
                "error": None,
            }

        # Check if user specifically requested alternatives
        if wants_alternatives:
            return {
                "input_kind": "alternatives",
                "wants_alternatives": True,
            }

        # Check if user explicitly asked to search/check a different product by name
        lowered = text.lower()
        search_prefixes = ("check ", "search ", "look up ", "find ", "analyze ")
        for prefix in search_prefixes:
            if lowered.startswith(prefix):
                new_query = text[len(prefix) :].strip()
                if new_query:
                    return {
                        "input_kind": "text",
                        "product_query": new_query,
                        "wants_alternatives": False,
                        "product": None,
                        "candidates": [],
                        "error": None,
                    }

        # Default for an active product: answer follow-up questions conversationally
        return {
            "input_kind": "followup_qa",
            "wants_alternatives": False,
        }

    # First turn in a conversation
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
