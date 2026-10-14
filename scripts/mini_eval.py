import argparse
import time

import pyarrow.parquet as pq
from labellens.config import settings
from labellens.embeddings.text import BgeTextEmbedder
from labellens.ids import point_id
from labellens.retrieval.qdrant_setup import get_client
from qdrant_client import models


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--collection", default=settings.products_collection)
    ap.add_argument("--text-model", default=settings.text_embed_model)
    ap.add_argument("--no-prefix", action="store_true")
    ap.add_argument("--ef", type=int, default=None)
    ap.add_argument("--rescore", action="store_true")
    ap.add_argument("--n", type=int, default=300)
    args = ap.parse_args()

    client = get_client()
    emb = BgeTextEmbedder(model_name=args.text_model, use_query_prefix=not args.no_prefix)

    schema_names = pq.read_schema(settings.clean_products_path).names
    brand_col = "brand" if "brand" in schema_names else "brands"
    table = pq.read_table(settings.clean_products_path, columns=["code", "name", brand_col])
    rows = table.slice(
        0, args.n
    ).to_pylist()  # first N: make sure they are indexed (use the same --limit)

    params = models.SearchParams(
        hnsw_ef=args.ef,
        quantization=models.QuantizationSearchParams(rescore=True) if args.rescore else None,
    )

    hits1 = hits5 = hits10 = 0
    rr_sum = 0.0
    t0 = time.perf_counter()
    for r in rows:
        brand = r.get("brand") or r.get("brands") or ""
        name = r.get("name") or ""
        query = f"{brand} {name}".strip()
        res = client.query_points(
            collection_name=args.collection,
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
    print(
        f"collection={args.collection} model={args.text_model} prefix={not args.no_prefix} ef={args.ef} rescore={args.rescore}"
    )
    print(
        f"Recall@1={hits1 / n:.3f}  Recall@5={hits5 / n:.3f}  Recall@10={hits10 / n:.3f}  MRR={rr_sum / n:.3f}"
    )
    print(f"avg latency (incl. query embedding): {elapsed / n * 1000:.1f} ms")


if __name__ == "__main__":
    main()
