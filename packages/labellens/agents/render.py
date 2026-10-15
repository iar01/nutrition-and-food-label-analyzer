from typing import Any

from labellens.agents.state import AgentState

LABEL = {
    "suitable": "suitable",
    "not_suitable": "NOT suitable",
    "unknown": "unknown, check the pack",
    "contains": "CONTAINS",
    "may_contain": "may contain traces",
    "not_listed": "not listed in the data",
}
OVERALL = {
    "not_suitable": "Not suitable for your profile",
    "check": "Needs a check: some information is missing or uncertain",
    "no_conflicts_found": "No conflicts found in the data",
    "no_profile": "No diet or allergen profile was given",
}


def fallback_summary(state: AgentState) -> str:
    product = state["product"] or {}
    verdicts = state["verdicts"]
    parts = [f"{product.get('name')}: {OVERALL[verdicts['overall']].lower()}."]
    for allergen, r in verdicts["allergens"].items():
        parts.append(f"{allergen}: {LABEL[r['status']]}.")
    for diet, r in verdicts["diets"].items():
        parts.append(f"{diet.replace('_', ' ')}: {LABEL[r['status']]}.")
    return " ".join(parts)


def render_answer(state: AgentState, summary: str, tips: list[str] | None = None) -> str:
    product = state["product"] or {}
    verdicts = state["verdicts"]
    findings: dict[str, Any] = state.get("findings", {})
    lines = [
        f"# {product.get('name')} ({product.get('brand') or 'unknown brand'})",
        "",
        summary,
        "",
    ]
    lines.append(f"**Overall:** {OVERALL[verdicts['overall']]}")
    lines.append("")

    if verdicts["allergens"] or verdicts["diets"]:
        lines += ["## Your profile", "", "| Check | Result | Why |", "|---|---|---|"]
        for allergen, r in verdicts["allergens"].items():
            lines.append(
                f"| Allergen: {allergen} | {LABEL[r['status']]} | {' '.join(r['reasons'])} |"
            )
        for diet, r in verdicts["diets"].items():
            lines.append(
                f"| Diet: {diet.replace('_', ' ')} | {LABEL[r['status']]} | {' '.join(r['reasons'])} |"
            )
        lines.append("")

    lines += ["## Nutrition per 100 g", ""]
    for nutrient, r in verdicts["nutrition"].items():
        value = "n/a" if r["value"] is None else f"{r['value']:.1f} g"
        lines.append(f"- {nutrient.replace('_g', '').replace('_', ' ')}: {value} ({r['level']})")
    lines.append(
        f"- Nutri-Score: {(product.get('nutriscore_grade') or 'unknown').upper()} | NOVA group: {product.get('nova_group') or 'unknown'}"
    )
    lines.append("")

    ingredients = findings.get("ingredients")
    if ingredients:
        lines += ["## Ingredients", "", ingredients["summary"], ""]
        for n in ingredients.get("notable", []):
            cites = f" [{', '.join(n['evidence_ids'])}]" if n["evidence_ids"] else ""
            lines.append(f"- **{n['item']}**: {n['why']}{cites}")
        lines.append("")

    additives = findings.get("additives")
    if additives and (additives["notes"] or additives["missing"]):
        lines += ["## Additives", ""]
        for n in additives["notes"]:
            extra = f" {n['relevant_to_user']}" if n.get("relevant_to_user") else ""
            lines.append(f"- **{n['e_number']}**: {n['explanation']}{extra} [{n['evidence_id']}]")
        for code in additives["missing"]:
            lines.append(f"- **{code}**: no explanation card available yet.")
        lines.append("")

    if state.get("alternatives"):
        lines += ["## Better-scoring alternatives that fit your profile", ""]
        for a in state["alternatives"]:
            lines.append(
                f"- {a['name']} ({a.get('brand')}), Nutri-Score {(a.get('nutriscore') or '?').upper()}"
            )
        lines.append("")

    if tips:
        lines += ["## Tips", ""] + [f"- {t}" for t in tips] + [""]

    seen: set[str] = set()
    lines += ["## Sources", ""]
    for e in state.get("evidence", []):
        if e["id"] in seen:
            continue
        seen.add(e["id"])
        link = f" ({e['source_url']})" if e.get("source_url") else ""
        lines.append(f"- [{e['id']}] {e['title']}{link}")
    lines += [
        "",
        "Product data comes from Open Food Facts (ODbL), a crowd-sourced database that can contain mistakes. "
        "This is general information, not medical advice. Always check the pack if you have an allergy.",
    ]
    return "\n".join(lines)
