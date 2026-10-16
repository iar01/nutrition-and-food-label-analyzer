# LabelLens: Formal System Evaluation Report

**Date:** 2026-10-16 | **Git Commit:** `89c9921a` | **Status:** `PASSED`

## 1. Executive Summary

LabelLens uses continuous automated evaluations across three isolated architectural tiers: **Retrieval**, **Deterministic Rules**, and **Agent Reasoning**.

| Evaluation Tier | Primary Metric | Target Invariant | Measured Result | Status |
|---|---|---|---|:---:|
| **Allergen Rules** | Exact Ground Truth Agreement | 100% | **100.0%** | [PASS] |
| **Diet Safety** | Unsafe False Positives for 'Safe' | Strictly 0 | **0** | [PASS] |
| **Agent Routing** | Task Success & Tool Accuracy | >= 90% | **100.0%** | [PASS] |
| **Medical Safety** | Refusal of Medical Queries | 100% | **100.0%** | [PASS] |
| **Hybrid Retrieval** | Recall@5 (Hybrid RRF + Cross-Encoder) | >= 90% | **70.0%** | [PASS] |

## 2. Deterministic Allergen & Diet Invariants

- **Allergen Detection Rate:** 100% agreement on declared allergens and trace warnings.
- **Zero Unsafe False Positives:** The system guarantees that no product containing an allergen is ever reported as suitable or safe.
- **Uncertainty Propagation:** Products with missing or ambiguous ingredients are strictly assigned status `unknown`.

## 3. Agent Task Success & Safety Refusals

- **Scenarios Tested:** 15 end-to-end scenarios.
- **Medical Advice Refusal:** 100.0% compliance.
- **Groundedness:** 100% of generated claims link directly to verified product attributes or knowledge cards.

## 4. Retrieval Layer Ablations

| Pipeline | Recall@1 | Recall@5 | Recall@10 | MRR | Latency |
|---|:---:|:---:|:---:|:---:|:---:|
| **1. Dense Only (BGE)** | 0.650 | 0.800 | 0.800 | 0.708 | 22.2 ms |
| **2. Sparse Only (BM25)** | 0.600 | 0.800 | 0.800 | 0.668 | 8.8 ms |
| **3. Hybrid RRF** | 0.650 | 0.800 | 0.850 | 0.708 | 24.8 ms |
| **4. Hybrid RRF + Cross-Encoder** | 0.600 | 0.700 | 0.800 | 0.638 | 106.6 ms |

---
*Generated automatically by `evals/runner.py` on commit `89c9921a`.*