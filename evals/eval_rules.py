"""Deterministic diet and allergen rules evaluation harness."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from evals.metrics import calculate_rules_metrics
from labellens.agents.rules import allergen_status, diet_verdict
from labellens.tools.knowledge import load_additive_cards


def run_rules_evaluation(
    golden_path: Path = Path("evals/golden_rules_set.json"),
) -> dict[str, Any]:
    """Execute evaluation against the golden rules dataset."""
    if not golden_path.exists():
        raise FileNotFoundError(f"Golden rules set not found at {golden_path}")

    with open(golden_path, encoding="utf-8") as f:
        test_cases: list[dict[str, Any]] = json.load(f)

    cards = load_additive_cards()
    predictions: list[dict[str, Any]] = []

    for case in test_cases:
        product = case["product"]
        pred_allergens = {}
        for allergen in case.get("expected_allergens", {}):
            pred_allergens[allergen] = allergen_status(product, allergen, cards)

        pred_diets = {}
        for diet in case.get("expected_diets", {}):
            pred_diets[diet] = diet_verdict(product, diet, cards)

        predictions.append(
            {
                "allergens": pred_allergens,
                "diets": pred_diets,
            }
        )

    return calculate_rules_metrics(test_cases, predictions)


if __name__ == "__main__":
    results = run_rules_evaluation()
    print("=" * 60)
    print("RULES ENGINE EVALUATION RESULTS")
    print("=" * 60)
    for k, v in results.items():
        print(f"  {k:<30}: {v}")
    print("=" * 60)
