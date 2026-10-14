import json
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq
from labellens.config import settings
from labellens.embeddings.text import BgeTextEmbedder
from labellens.ids import point_id
from labellens.retrieval.qdrant_setup import get_client
from qdrant_client import QdrantClient, models


def run_eval(
    client: QdrantClient,
    rows: Sequence[dict[str, Any]],
    collection_name: str,
    text_model: str,
    use_prefix: bool,
    ef: int | None = None,
    rescore: bool = False,
    emb_cache: dict[tuple[str, bool], BgeTextEmbedder] | None = None,
) -> dict[str, Any]:
    cache_key = (text_model, use_prefix)
    if emb_cache is not None and cache_key in emb_cache:
        emb = emb_cache[cache_key]
    else:
        emb = BgeTextEmbedder(model_name=text_model, use_query_prefix=use_prefix)
        if emb_cache is not None:
            emb_cache[cache_key] = emb

    params = models.SearchParams(
        hnsw_ef=ef,
        quantization=models.QuantizationSearchParams(rescore=True) if rescore else None,
    )

    hits1 = hits5 = hits10 = 0
    rr_sum = 0.0
    t0 = time.perf_counter()
    for r in rows:
        brand = r.get("brand") or r.get("brands") or ""
        name = r.get("name") or ""
        query = f"{brand} {name}".strip()
        res = client.query_points(
            collection_name=collection_name,
            query=emb.embed_query(query).tolist(),
            using="text_dense",
            limit=10,
            search_params=params,
        ).points
        ids = [p.id for p in res]
        target = point_id(r["code"])
        if target in ids:
            rank = ids.index(target) + 1
            rr_sum += 1 / rank
            hits1 += rank == 1
            hits5 += rank <= 5
            hits10 += rank <= 10
    elapsed = time.perf_counter() - t0
    n = len(rows)

    metrics = {
        "collection": collection_name,
        "model": text_model,
        "prefix": use_prefix,
        "ef": ef,
        "rescore": rescore,
        "recall_1": round(hits1 / n, 4),
        "recall_5": round(hits5 / n, 4),
        "recall_10": round(hits10 / n, 4),
        "mrr": round(rr_sum / n, 4),
        "latency_ms": round(elapsed / n * 1000, 2),
    }
    print(
        f"{collection_name} | {text_model.split('/')[-1]} | prefix={use_prefix} | ef={ef} | rescore={rescore} -> "
        f"R@1={metrics['recall_1']:.3f} R@5={metrics['recall_5']:.3f} MRR={metrics['mrr']:.3f} Lat={metrics['latency_ms']:.1f}ms"
    )
    return metrics


def main() -> None:
    client = get_client()
    schema_names = pq.read_schema(settings.clean_products_path).names
    brand_col = "brand" if "brand" in schema_names else "brands"
    table = pq.read_table(settings.clean_products_path, columns=["code", "name", brand_col])
    rows = table.slice(0, 300).to_pylist()

    emb_cache = {}
    results = {}

    print("--- 1. Baseline (bge-small, with prefix, ef=None, quant=off) ---")
    results["baseline"] = run_eval(
        client, rows, "products", settings.text_embed_model, use_prefix=True, emb_cache=emb_cache
    )

    print("\n--- 2. Experiment A: Query Prefix (without prefix) ---")
    results["no_prefix"] = run_eval(
        client, rows, "products", settings.text_embed_model, use_prefix=False, emb_cache=emb_cache
    )

    print("\n--- 3. Experiment B: bge-base (768-d) vs bge-small (384-d) ---")
    results["bge_base"] = run_eval(
        client,
        rows,
        "products_bge_base",
        "BAAI/bge-base-en-v1.5",
        use_prefix=True,
        emb_cache=emb_cache,
    )

    print("\n--- 4. Experiment C: HNSW ef exploration ---")
    for ef in [16, 64, 256]:
        results[f"ef_{ef}"] = run_eval(
            client,
            rows,
            "products",
            settings.text_embed_model,
            use_prefix=True,
            ef=ef,
            emb_cache=emb_cache,
        )

    print("\n--- 5. Experiment D: Scalar Quantization ---")
    # Enable scalar quantization on products collection
    print("Applying INT8 Scalar Quantization to 'products' collection...")
    client.update_collection(
        collection_name="products",
        quantization_config=models.ScalarQuantization(
            scalar=models.ScalarQuantizationConfig(
                type=models.ScalarType.INT8, quantile=0.99, always_ram=True
            )
        ),
    )
    # Give Qdrant a moment to complete quantization indexing
    time.sleep(3)

    results["quant_off"] = results["baseline"]
    print("Evaluating with quantization ON, rescore=False...")
    results["quant_on_no_rescore"] = run_eval(
        client,
        rows,
        "products",
        settings.text_embed_model,
        use_prefix=True,
        rescore=False,
        emb_cache=emb_cache,
    )
    print("Evaluating with quantization ON, rescore=True...")
    results["quant_on_rescore"] = run_eval(
        client,
        rows,
        "products",
        settings.text_embed_model,
        use_prefix=True,
        rescore=True,
        emb_cache=emb_cache,
    )

    out_path = Path("notebooks/experiment_results.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(results, indent=2))
    print(f"\nAll experiments complete! Results saved to {out_path}")


if __name__ == "__main__":
    main()
