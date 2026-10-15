import json
import logging
import re
from typing import Any

from labellens.agents.deps import Deps
from labellens.agents.prompts import SUMMARY_SYSTEM
from labellens.agents.render import fallback_summary, render_answer
from labellens.agents.schemas import FinalSummary
from labellens.agents.state import AgentState
from labellens.llm.structured import structured_call
from langchain_core.messages import AIMessage

logger = logging.getLogger(__name__)
BANNED = re.compile(
    r"\b(safe|safely|guarantee\w*|cure\w*|treat(s|ed|ment)?|diagnos\w*|doctor|medical advice)\b",
    re.IGNORECASE,
)
MAX_REVISIONS = 1


def synthesizer(state: AgentState, deps: Deps) -> dict[str, Any]:
    product = state["product"] or {}
    verdicts = state["verdicts"]
    facts = {
        "product": product.get("name"),
        "brand": product.get("brand"),
        "overall": verdicts["overall"],
        "diets": {d: r["status"] for d, r in verdicts["diets"].items()},
        "allergens": {a: r["status"] for a, r in verdicts["allergens"].items()},
        "goals": verdicts["goals"],
        "nutrition_levels": {k: v["level"] for k, v in verdicts["nutrition"].items()},
        "nutriscore": product.get("nutriscore_grade"),
        "nova": product.get("nova_group"),
        "alternatives": [a["name"] for a in state.get("alternatives", [])],
    }
    user = json.dumps(facts)
    feedback = state.get("critic_feedback")
    if feedback:
        user += f"\nFix these problems from your last attempt: {feedback}"

    summary: str
    tips: list[str]
    try:
        result = structured_call(deps.llm, FinalSummary, SUMMARY_SYSTEM, user)
        summary, tips = result.summary, result.tips
    except Exception:
        logger.warning("synthesizer fell back to a template", exc_info=True)
        summary, tips = fallback_summary(state), []
    return {
        "draft": {"summary": summary, "tips": tips},
        "answer": render_answer(state, summary, tips),
    }


def critic(state: AgentState, deps: Deps) -> dict[str, Any]:
    draft = state.get("draft", {})
    text = f"{draft.get('summary', '')} {' '.join(draft.get('tips', []))}"
    issues: list[str] = []

    if BANNED.search(text):
        issues.append("Remove words like safe, guarantee, treat, diagnose or doctor.")
    for allergen, r in state["verdicts"]["allergens"].items():
        if (
            r["status"] in ("contains", "may_contain")
            and allergen.replace("_", " ") not in text.lower()
        ):
            issues.append(f"The summary must mention the {allergen} allergen finding.")

    revisions = state.get("revisions", 0)
    if not issues:
        return {"critic_feedback": None, "messages": [AIMessage(content=state.get("answer") or "")]}
    if revisions < MAX_REVISIONS:
        return {"critic_feedback": " ".join(issues), "revisions": revisions + 1}

    summary = fallback_summary(state)  # out of retries: use the template
    answer = render_answer(state, summary)
    return {
        "critic_feedback": None,
        "draft": {"summary": summary, "tips": []},
        "answer": answer,
        "messages": [AIMessage(content=answer)],
    }
