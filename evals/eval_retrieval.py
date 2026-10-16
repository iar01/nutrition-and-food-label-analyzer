"""Retrieval evaluation harness measuring Recall@1/5/10, MRR, nDCG, and latency."""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from evals.metrics import calculate_retrieval_metrics
from labellens.config import settings
from labellens.embeddings.sparse import Bm25SparseEmbedder
from labellens.embeddings.text import BgeTextEmbedder
from labellens.ids import point_id
from labellens.retrieval.hybrid import HybridRetriever
from labellens.retrieval.models import SearchHit
from labellens.retrieval.qdrant_setup import get_client
from labellens.retrieval.reranker import CrossEncoderReranker


def evaluate_pipeline_on_queries(
    name: str,
    queries: list[dict[str, Any]],
    search_fn: Callable[[str], list[str]],
) -> dict[str, Any]:
    """Evaluate a search function against a set of queries."""
    latencies: list[float] = []
    retrieved_results: list[list[str]] = []

    # Map target_code to point_id for matching Qdrant IDs
    normalized_queries = []
    for q in queries:
        target_id = point_id(q["target_code"])
        normalized_queries.append({**q, "target_id": target_id})

    for q in normalized_queries:
        t0 = time.perf_counter()
        hits = search_fn(q["query"])
        latencies.append((time.perf_counter() - t0) * 1000)
        retrieved_results.append(hits[:10])

    metrics = calculate_retrieval_metrics(normalized_queries, retrieved_results, latencies)
    metrics["pipeline"] = name

    # Also compute breakdown by query_type
    query_types = {q.get("query_type", "unknown") for q in queries}
    breakdown = {}
    for qt in sorted(query_types):
        sub_queries = [
            q for q in normalized_queries if q.get("query_type", "unknown") == qt
        ]
        sub_results = [
            retrieved_results[i]
            for i, q in enumerate(normalized_queries)
            if q.get("query_type", "unknown") == qt
        ]
        sub_metrics = calculate_retrieval_metrics(sub_queries, sub_results)
        breakdown[qt] = {
            "count": len(sub_queries),
            "recall_1": sub_metrics["recall_1"],
            "recall_5": sub_metrics["recall_5"],
            "mrr": sub_metrics["mrr"],
        }
    metrics["breakdown_by_query_type"] = breakdown

    return metrics


def run_retrieval_evaluation(
    golden_path: Path = Path("evals/golden_retrieval_set.jsonl"),
    limit: int | None = None,
) -> list[dict[str, Any]]:
    """Run full ablation evaluation on golden retrieval queries."""
    if not golden_path.exists():
        raise FileNotFoundError(f"Golden retrieval set not found at {golden_path}")

    with open(golden_path, encoding="utf-8") as f:
        queries = [json.loads(line) for line in f]

    if limit is not None:
        queries = queries[:limit]

    client = get_client()
    text_emb = BgeTextEmbedder()
    sparse_emb = Bm25SparseEmbedder()
    hybrid = HybridRetriever(client, text_embedder=text_emb, sparse_embedder=sparse_emb)
    reranker = CrossEncoderReranker()

    def search_dense(q: str) -> list[str]:
        vec = text_emb.embed_query(q).tolist()
        res = client.query_points(
            collection_name=settings.products_collection,
            query=vec,
            using="text_dense",
            limit=10,
            with_payload=False,
        ).points
        return [str(p.id) for p in res]

    def search_sparse(q: str) -> list[str]:
        vec = sparse_emb.embed_query(q)
        res = client.query_points(
            collection_name=settings.products_collection,
            query=vec,
            using="bm25",
            limit=10,
            with_payload=False,
        ).points
        return [str(p.id) for p in res]

    def search_hybrid(q: str) -> list[str]:
        hits: list[SearchHit] = hybrid.search(q, limit=10)
        return [h.id for h in hits]

    def search_hybrid_rerank(q: str) -> list[str]:
        candidates: list[SearchHit] = hybrid.search(q, limit=20)
        reranked = reranker.rerank(q, candidates, top_k=10)
        return [h.id for h in reranked]

    results = [
        evaluate_pipeline_on_queries("1. Dense Only (BGE)", queries, search_dense),
        evaluate_pipeline_on_queries("2. Sparse Only (BM25)", queries, search_sparse),
        evaluate_pipeline_on_queries("3. Hybrid RRF", queries, search_hybrid),
        evaluate_pipeline_on_queries(
            "4. Hybrid RRF + Cross-Encoder", queries, search_hybrid_rerank
        ),
    ]

    return results


if __name__ == "__main__":
    ablations = run_retrieval_evaluation(limit=25)
    print("=" * 85)
    print(
        f"{'Pipeline':<32} | {'Recall@1':<8} | {'Recall@5':<8} | {'Recall@10':<9} | {'MRR':<6} | {'Avg Latency'}"
    )
    print("-" * 85)
    for r in ablations:
        print(
            f"{r['pipeline']:<32} | {r['recall_1']:<8.3f} | {r['recall_5']:<8.3f} | {r['recall_10']:<9.3f} | {r['mrr']:<6.3f} | {r.get('latency_avg_ms', 0):.1f} ms"
        )
    print("=" * 85)
