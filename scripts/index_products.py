import argparse

import pyarrow.parquet as pq
from qdrant_client import models
from tqdm import tqdm

from labellens.config import settings
from labellens.embeddings.sparse import Bm25SparseEmbedder
from labellens.embeddings.text import BgeTextEmbedder
from labellens.ids import point_id
from labellens.retrieval.qdrant_setup import create_products_collection, get_client
import math

# Left: the key this script uses. Right: the column in YOUR parquet.
COLUMN_MAP = {
    "code": "code",
    "name": "name",
    "brands": "brand",
    "categories": "categories_tags",
    "allergens": "allergens_tags",
    "nutriscore": "nutriscore_grade",
    "nova": "nova_group",
    "diet_vegan": "diet_vegan",
    "diet_vegetarian": "diet_vegetarian",
    "diet_gluten_free": "diet_gluten_free",
    "diet_lactose_free": "diet_lactose_free",
    "diet_palm_oil_free": "diet_palm_oil_free",
    "diet_nut_free": "diet_nut_free",
    "energy_kcal": "energy_kcal",
    "fat_g": "fat_g",
    "sat_fat_g": "sat_fat_g",
    "carbs_g": "carbs_g",
    "sugars_g": "sugars_g",
    "protein_g": "protein_g",
    "salt_g": "salt_g",
    "search_text": "search_text",
}
COLUMNS = list(COLUMN_MAP.values())

def _num(x: float | None) -> float | None:
    """Float or None (turns NaN into None, because NaN breaks JSON)."""
    if x is None or math.isnan(x):
        return None
    return float(x)


def _int(x: float | None) -> int | None:
    v = _num(x)
    return int(v) if v is not None else None


def make_payload(row: dict) -> dict:
    return {
        "code": row["code"],
        "name": row["name"],
        "brands": row["brands"],
        "categories": row["categories"] or [],
        "allergens": row["allergens"] or [],
        "nutriscore": row["nutriscore"],
        "nova": _int(row["nova"]),
        "diet_vegan": row["diet_vegan"],
        "diet_vegetarian": row["diet_vegetarian"],
        "diet_gluten_free": row["diet_gluten_free"],
        "diet_lactose_free": row["diet_lactose_free"],
        "diet_palm_oil_free": row["diet_palm_oil_free"],
        "diet_nut_free": row["diet_nut_free"],
        "energy_kcal": _num(row["energy_kcal"]),
        "fat_g": _num(row["fat_g"]),
        "sat_fat_g": _num(row["sat_fat_g"]),
        "carbs_g": _num(row["carbs_g"]),
        "sugars_g": _num(row["sugars_g"]),
        "protein_g": _num(row["protein_g"]),
        "salt_g": _num(row["salt_g"]),
        "has_image": False,  # Pass 2 flips this to True
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None, help="only index the first N products")
    ap.add_argument("--batch-size", type=int, default=256)
    ap.add_argument("--collection", default=settings.products_collection)
    ap.add_argument("--text-model", default=settings.text_embed_model)
    ap.add_argument("--recreate", action="store_true", help="delete and recreate the collection first")
    args = ap.parse_args()

    client = get_client()
    text_emb = BgeTextEmbedder(model_name=args.text_model)
    sparse_emb = Bm25SparseEmbedder()
    create_products_collection(client, name=args.collection, text_dim=text_emb.dim, recreate=args.recreate)

    pf = pq.ParquetFile(settings.clean_products_path)
    total = min(pf.metadata.num_rows, args.limit or pf.metadata.num_rows)
    done = 0

    with tqdm(total=total, desc="indexing") as bar:
        for batch in pf.iter_batches(batch_size=args.batch_size, columns=COLUMNS):
            rows = batch.to_pylist()
            rows = [{key: row[col] for key, col in COLUMN_MAP.items()} for row in rows]  # NEW

            if args.limit is not None:
                rows = rows[: args.limit - done]
            if not rows:
                break

            texts = [r["search_text"] for r in rows]
            dense = text_emb.embed_documents(texts)
            sparse = sparse_emb.embed_documents(texts)

            points = [
                models.PointStruct(
                    id=point_id(r["code"]),
                    vector={"text_dense": dense[i].tolist(), "bm25": sparse[i]},
                    payload=make_payload(r),
                )
                for i, r in enumerate(rows)
            ]
            client.upsert(collection_name=args.collection, points=points, wait=True)

            done += len(rows)
            bar.update(len(rows))
            if args.limit is not None and done >= args.limit:
                break

    print("points in collection:", client.count(args.collection, exact=True).count)


if __name__ == "__main__":
    main()