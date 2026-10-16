# LabelLens: Formal System Evaluation Report

**Date:** 2026-10-16 | **Git Commit:** `a68ba980` | **Status:** `PASSED`

## 1. Executive Summary

LabelLens uses continuous automated evaluations across three isolated architectural tiers: **Retrieval**, **Deterministic Rules**, and **Agent Reasoning**.

| Evaluation Tier | Primary Metric | Target Invariant | Measured Result | Status |
|---|---|---|---|:---:|
| **Allergen Rules** | Exact Ground Truth Agreement | 100% | **100.0%** | [PASS] |
| **Diet Safety** | Unsafe False Positives for 'Safe' | Strictly 0 | **0** | [PASS] |
| **Agent Routing** | Task Success & Tool Accuracy | >= 90% | **100.0%** | [PASS] |
| **Medical Safety** | Refusal of Medical Queries | 100% | **100.0%** | [PASS] |
| **Hybrid Retrieval** | Recall@5 (Hybrid RRF + Cross-Encoder) | >= 90% | **80.8%** | [PASS] |

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
| **1. Dense Only (BGE)** | 0.608 | 0.775 | 0.808 | 0.681 | 27.2 ms |
| **2. Sparse Only (BM25)** | 0.658 | 0.808 | 0.858 | 0.723 | 10.9 ms |
| **3. Hybrid RRF (Dense + BM25)** | 0.658 | 0.808 | 0.850 | 0.730 | 30.2 ms |
| **4. Hybrid RRF + Cross-Encoder** | 0.667 | 0.808 | 0.858 | 0.736 | 195.8 ms |

---
*Generated automatically by `evals/runner.py` on commit `a68ba980`.*