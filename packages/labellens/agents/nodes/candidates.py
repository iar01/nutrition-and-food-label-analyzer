from typing import Any

from labellens.agents.deps import Deps
from labellens.agents.evidence import product_evidence
from labellens.agents.state import AgentState
from langgraph.types import interrupt


def find_candidates(state: AgentState, deps: Deps) -> dict[str, Any]:
    query = state.get("product_query") or ""
    if state.get("input_kind") == "barcode":
        for code in (query, query.zfill(13)):
            product = deps.repo.get(code)
            if product:
                return {
                    "candidates": [
                        {
                            "code": product["code"],
                            "name": product.get("name"),
                            "brands": product.get("brand"),
                        }
                    ]
                }
        return {"candidates": []}

    hits = deps.searcher.products(query, limit=5)
    return {
        "candidates": [{"code": h["code"], "name": h["name"], "brands": h["brands"]} for h in hits]
    }


def choose_product(state: AgentState, deps: Deps) -> dict[str, Any]:
    candidates = state.get("candidates") or []
    if not candidates:
        return {
            "error": "not_found",
            "answer": "I could not find a matching product in my data. Try the barcode or a more exact name.",
        }

    if len(candidates) == 1 or state.get("auto_pick"):
        code = candidates[0]["code"]
    else:
        picked = interrupt({"question": "Which product did you mean?", "candidates": candidates})
        code = str(picked.get("code", candidates[0]["code"]))
        if code not in {c["code"] for c in candidates}:
            code = candidates[0]["code"]

    product = deps.repo.get(code)
    if product is None:
        return {"error": "not_found", "answer": "That product is no longer in my data."}
    return {"product": product, "evidence": [product_evidence(product)]}
