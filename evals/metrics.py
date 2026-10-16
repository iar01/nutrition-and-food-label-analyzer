"""Evaluation metrics calculator for retrieval, rules, and agent pipelines."""

from __future__ import annotations

import math
from typing import Any


def calculate_retrieval_metrics(
    eval_items: list[dict[str, Any]],
    results: list[list[str]],
    latencies_ms: list[float] | None = None,
) -> dict[str, float]:
    """Calculate Recall@K, MRR, nDCG@10, and latency percentiles.

    Args:
        eval_items: List of dicts containing 'target_code' or 'target_id'.
        results: List of retrieved IDs/codes for each evaluation item.
        latencies_ms: Optional execution latencies in milliseconds.
    """
    n = len(eval_items)
    if n == 0:
        return {}

    hits1 = 0
    hits5 = 0
    hits10 = 0
    reciprocal_ranks = []
    ndcg_scores = []

    for item, retrieved in zip(eval_items, results, strict=False):
        target = item.get("target_id") or item.get("target_code")
        top10 = list(retrieved[:10])

        if target in top10:
            rank = top10.index(target) + 1
            reciprocal_ranks.append(1.0 / rank)
            hits1 += int(rank == 1)
            hits5 += int(rank <= 5)
            hits10 += int(rank <= 10)
            ndcg_scores.append(1.0 / math.log2(rank + 1))
        else:
            reciprocal_ranks.append(0.0)
            ndcg_scores.append(0.0)

    metrics = {
        "num_queries": float(n),
        "recall_1": round(hits1 / n, 4),
        "recall_5": round(hits5 / n, 4),
        "recall_10": round(hits10 / n, 4),
        "mrr": round(sum(reciprocal_ranks) / n, 4),
        "ndcg_10": round(sum(ndcg_scores) / n, 4),
    }

    if latencies_ms:
        sorted_lat = sorted(latencies_ms)
        metrics["latency_avg_ms"] = round(sum(latencies_ms) / n, 2)
        metrics["latency_p50_ms"] = round(sorted_lat[int(0.50 * n)], 2)
        metrics["latency_p90_ms"] = round(sorted_lat[int(0.90 * n)], 2)
        metrics["latency_p95_ms"] = round(sorted_lat[int(0.95 * n)], 2)

    return metrics


def calculate_rules_metrics(
    eval_cases: list[dict[str, Any]],
    predictions: list[dict[str, Any]],
) -> dict[str, Any]:
    """Evaluate deterministic allergen and diet rule predictions against ground truth."""
    n = len(eval_cases)
    if n == 0:
        return {}

    allergen_matches = 0
    total_allergen_checks = 0
    diet_matches = 0
    total_diet_checks = 0
    unsafe_false_positives = 0  # CRITICAL: Claimed safe/suitable when allergen was present

    for case, pred in zip(eval_cases, predictions, strict=False):
        expected_allergens = case.get("expected_allergens", {})
        pred_allergens = pred.get("allergens", {})
        for allergen, expected_status in expected_allergens.items():
            actual = pred_allergens.get(allergen, {}).get("status")
            total_allergen_checks += 1
            if actual == expected_status:
                allergen_matches += 1
            if expected_status in ("contains", "may_contain") and actual == "not_listed":
                unsafe_false_positives += 1

        expected_diets = case.get("expected_diets", {})
        pred_diets = pred.get("diets", {})
        for diet, expected_status in expected_diets.items():
            actual = pred_diets.get(diet, {}).get("status")
            total_diet_checks += 1
            if actual == expected_status:
                diet_matches += 1
            if expected_status == "not_suitable" and actual == "suitable":
                unsafe_false_positives += 1

    allergen_acc = allergen_matches / total_allergen_checks if total_allergen_checks > 0 else 1.0
    diet_acc = diet_matches / total_diet_checks if total_diet_checks > 0 else 1.0
    zero_false_positives = unsafe_false_positives == 0

    return {
        "num_test_cases": n,
        "total_allergen_checks": total_allergen_checks,
        "allergen_accuracy": round(allergen_acc, 4),
        "total_diet_checks": total_diet_checks,
        "diet_accuracy": round(diet_acc, 4),
        "unsafe_false_positives": unsafe_false_positives,
        "safety_invariant_passed": zero_false_positives,
    }


def calculate_agent_metrics(scenario_results: list[dict[str, Any]]) -> dict[str, Any]:
    """Calculate agent execution success, tool routing accuracy, and refusal compliance."""
    n = len(scenario_results)
    if n == 0:
        return {}

    successful = 0
    tool_routed_correctly = 0
    medical_refusals = 0
    medical_queries = 0
    evidence_grounded = 0

    for r in scenario_results:
        if r.get("success"):
            successful += 1
        if r.get("tool_correct"):
            tool_routed_correctly += 1
        if r.get("is_medical_query"):
            medical_queries += 1
            if r.get("refused_medical_advice"):
                medical_refusals += 1
        if r.get("grounded"):
            evidence_grounded += 1

    refusal_rate = medical_refusals / medical_queries if medical_queries > 0 else 1.0
    grounded_rate = evidence_grounded / n if n > 0 else 1.0

    return {
        "num_scenarios": n,
        "task_success_rate": round(successful / n, 4),
        "tool_routing_accuracy": round(tool_routed_correctly / n, 4),
        "medical_queries_tested": medical_queries,
        "medical_refusal_rate": round(refusal_rate, 4),
        "groundedness_rate": round(grounded_rate, 4),
    }
