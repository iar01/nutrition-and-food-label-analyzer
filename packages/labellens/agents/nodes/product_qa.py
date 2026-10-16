"""Node for answering follow-up questions about the active product in a conversation."""

from __future__ import annotations

import json
import logging
from typing import Any

from labellens.agents.deps import Deps
from labellens.agents.prompts import PRODUCT_QA_SYSTEM
from labellens.agents.state import AgentState
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

logger = logging.getLogger(__name__)


def product_qa(state: AgentState, deps: Deps) -> dict[str, Any]:
    """Provide a conversational answer to a user's follow-up question about the active product."""
    product = state.get("product") or {}
    profile = state.get("profile") or {}
    verdicts = state.get("verdicts") or {}
    findings = state.get("findings") or {}
    user_text = state.get("user_text", "").strip()

    context = {
        "product_name": product.get("name"),
        "brand": product.get("brand"),
        "ingredients": product.get("ingredients"),
        "nutriscore_grade": product.get("nutriscore_grade"),
        "nova_group": product.get("nova_group"),
        "nutrition_per_100g": {
            "energy_kcal": product.get("energy_kcal"),
            "sugars_g": product.get("sugars_g"),
            "fat_g": product.get("fat_g"),
            "sat_fat_g": product.get("sat_fat_g"),
            "salt_g": product.get("salt_g"),
            "protein_g": product.get("protein_g"),
        },
        "declared_allergens": product.get("allergens_tags", []),
        "declared_additives": product.get("additives_tags", []),
        "user_profile": profile,
        "verdicts": verdicts,
        "findings": findings,
    }

    prompt = f"Product Data:\n{json.dumps(context, indent=2)}\n\nUser Question: {user_text}"

    try:
        messages = [
            SystemMessage(content=PRODUCT_QA_SYSTEM),
            HumanMessage(content=prompt),
        ]
        raw_reply = str(deps.llm.invoke(messages).content).strip()
        reply = raw_reply
    except Exception:
        logger.warning("product_qa LLM call failed, providing fallback", exc_info=True)
        ing_clean = (
            product.get("ingredients") or "the ingredients listed in the product overview"
        ).rstrip(".")
        reply = (
            f"Based on the label for **{product.get('name', 'this product')}**, "
            f"it contains {ing_clean}. "
            "Please check the physical packaging for the most current details."
        )

    disclaimer = (
        "\n\n> ⚠️ **Educational & Learning Project Notice**: Not health advice. "
        "Always consult a healthcare professional and check physical packaging."
    )
    if "Educational & Learning Project Notice" not in reply:
        reply += disclaimer

    return {
        "answer": reply,
        "messages": [AIMessage(content=reply)],
    }
