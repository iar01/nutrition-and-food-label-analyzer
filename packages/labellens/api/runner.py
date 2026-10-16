import json
import logging
from collections.abc import Iterator
from typing import Any

from langchain_core.messages import HumanMessage

from labellens.agents.schemas import IngredientFindings
from labellens.api.schemas import (
    AdditiveSection,
    AlternativeOut,
    AnalysisOut,
    EvidenceOut,
    ProductSummary,
    Verdicts,
)
from labellens.cache import SemanticHit

logger = logging.getLogger("labellens.api")

NUTRITION_KEYS = ("energy_kcal", "fat_g", "sat_fat_g", "carbs_g", "sugars_g", "protein_g", "salt_g")

STEP_LABELS = {
    "router": "Understanding your request",
    "find_candidates": "Searching products",
    "choose_product": "Loading the product",
    "ingredient_analyst": "Reading the ingredients",
    "additive_analyst": "Checking additives",
    "diet_checker": "Checking your diet and allergens",
    "join": "Combining the results",
    "alternatives": "Looking for better options",
    "synthesizer": "Writing the summary",
    "critic": "Reviewing the answer",
}


def initial_state(text: str, profile: dict[str, Any], auto_pick: bool) -> dict[str, Any]:
    return {
        "user_text": text,
        "messages": [HumanMessage(content=text)],
        "profile": profile,
        "auto_pick": auto_pick,
        "evidence": [],
        "findings": {},
        "revisions": 0,
        "error": None,
        "critic_feedback": None,
    }


def to_product_summary(product: dict[str, Any]) -> ProductSummary:
    nova = product.get("nova_group")
    return ProductSummary(
        code=product["code"],
        name=product.get("name"),
        brand=product.get("brand"),
        quantity=product.get("quantity"),
        ingredients=product.get("ingredients"),
        nutriscore=product.get("nutriscore_grade") or None,
        nova_group=int(nova) if nova is not None else None,
        categories=product.get("categories_tags") or [],
        allergens=product.get("allergens_tags") or [],
        traces=product.get("traces_tags") or [],
        additives=product.get("additives_tags") or [],
        nutrition_per_100g={k: product.get(k) for k in NUTRITION_KEYS},
        off_url=f"https://world.openfoodfacts.org/product/{product['code']}",
    )


def to_analysis(values: dict[str, Any]) -> AnalysisOut:
    findings: dict[str, Any] = values.get("findings", {})
    draft: dict[str, Any] = values.get("draft") or {}
    seen: set[str] = set()
    evidence: list[EvidenceOut] = []
    for item in values.get("evidence", []):
        if item["id"] not in seen:
            seen.add(item["id"])
            evidence.append(EvidenceOut(**item))
    return AnalysisOut(
        product=to_product_summary(values["product"]),
        verdicts=Verdicts.model_validate(values["verdicts"]),
        summary=str(draft.get("summary", "")),
        tips=list(draft.get("tips", [])),
        ingredients=IngredientFindings.model_validate(findings["ingredients"])
        if findings.get("ingredients")
        else None,
        additives=AdditiveSection.model_validate(findings["additives"])
        if findings.get("additives")
        else None,
        alternatives=[AlternativeOut(**a) for a in values.get("alternatives", [])],
        evidence=evidence,
        answer_markdown=values.get("answer") or "",
    )


# ------------------------------------------------------------------ SSE (Lesson 6)
def sse(event: str, data: dict[str, Any]) -> str:
    """One Server-Sent Event: a named event, one line of JSON data, and a blank line."""
    return f"event: {event}\ndata: {json.dumps(data, default=str)}\n\n"


def cached_chat_events(thread_id: str, analysis: AnalysisOut) -> Iterator[str]:
    """Emit Server-Sent Events from a cached AnalysisOut instantly."""
    yield sse("step", {"node": "cache", "label": "Retrieved from instant cache"})
    for part in analysis.answer_markdown.split("\n\n"):
        yield sse("answer_chunk", {"text": part + "\n\n"})
    yield sse("final", {"thread_id": thread_id, **analysis.model_dump()})
    yield sse("done", {"thread_id": thread_id, "status": "complete"})


def semantic_cached_chat_events(thread_id: str, hit: SemanticHit) -> Iterator[str]:
    """Emit Server-Sent Events from a semantic cache hit."""
    percent = int(round(hit.similarity * 100))
    yield sse(
        "step",
        {
            "node": "semantic_cache",
            "label": f"Retrieved from semantic cache ({percent}% match with '{hit.matched_query}')",
        },
    )
    for part in hit.answer.split("\n\n"):
        yield sse("answer_chunk", {"text": part + "\n\n"})
    if hit.analysis:
        yield sse("final", {"thread_id": thread_id, **hit.analysis})
    else:
        yield sse("final", {"thread_id": thread_id, "answer_markdown": hit.answer})
    yield sse("done", {"thread_id": thread_id, "status": "complete"})


def chat_events(
    graph: Any,
    inputs: Any,
    config: dict[str, Any],
    thread_id: str,
    cache: Any = None,
    semantic_cache: Any = None,
    embedder: Any = None,
) -> Iterator[str]:
    """Run the graph and yield SSE strings. This is a plain (blocking) generator."""
    try:
        for chunk in graph.stream(inputs, config, stream_mode="updates"):
            for node in chunk:
                if node == "__interrupt__":
                    payload = chunk["__interrupt__"][0].value
                    yield sse(
                        "choose_product",
                        {
                            "thread_id": thread_id,
                            "question": payload["question"],
                            "candidates": payload["candidates"],
                        },
                    )
                    yield sse("done", {"thread_id": thread_id, "status": "waiting_for_choice"})
                    return
                yield sse("step", {"node": node, "label": STEP_LABELS.get(node, node)})

        values = graph.get_state(config).values
        if values.get("error") or not values.get("product"):
            yield sse(
                "error",
                {
                    "error": values.get("error") or "not_found",
                    "message": values.get("answer") or "No product found.",
                },
            )
            yield sse("done", {"thread_id": thread_id, "status": "failed"})
            return

        analysis = to_analysis(values)
        product_code = values.get("product", {}).get("code")
        profile = values.get("profile") or (
            inputs.get("profile") if isinstance(inputs, dict) else None
        )

        if cache is not None and product_code:
            cache.set(product_code, profile, analysis)

        if semantic_cache is not None and product_code and embedder is not None:
            user_text = inputs.get("user_text", "") if isinstance(inputs, dict) else ""
            if user_text:
                try:
                    if hasattr(embedder, "embed_query"):
                        raw_vec = embedder.embed_query(user_text)
                    else:
                        raw_vec = embedder.embed_text([user_text])[0]
                    vec = raw_vec.tolist() if hasattr(raw_vec, "tolist") else list(raw_vec)
                    semantic_cache.set(
                        query=user_text,
                        product_code=product_code,
                        profile=profile,
                        answer=analysis.answer_markdown,
                        vector=vec,
                        metadata={"analysis": analysis.model_dump()},
                    )
                except Exception:
                    logger.debug("Failed to set semantic cache entry", exc_info=True)

        # The answer is assembled by code, so we stream it paragraph by paragraph.
        for part in analysis.answer_markdown.split("\n\n"):
            yield sse("answer_chunk", {"text": part + "\n\n"})
        yield sse("final", {"thread_id": thread_id, **analysis.model_dump()})
        yield sse("done", {"thread_id": thread_id, "status": "complete"})
    except Exception:
        logger.exception("chat stream failed")
        yield sse("error", {"error": "internal_error", "message": "Something went wrong."})
        yield sse("done", {"thread_id": thread_id, "status": "failed"})
