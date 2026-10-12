"""Bulk data loader and benchmarking utility for PostgreSQL."""

import math
import time
from pathlib import Path
from typing import Any

import pandas as pd
import psycopg
from sqlalchemy import func, insert, select

from labellens.config import get_settings
from labellens.db.models import (
    Additive,
    Nutrition,
    Product,
    ProductDietFlag,
)
from labellens.db.session import SyncSessionLocal

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PARQUET = (PROJECT_ROOT / "data" / "clean" / "products.parquet").as_posix()
BENCHMARK_REPORT = (PROJECT_ROOT / "docs" / "bulk_load_benchmarks.md").as_posix()


def _sanitize_float(val: Any) -> float | None:
    if val is None or not isinstance(val, (int, float)) or math.isnan(val):
        return None
    return float(val)


def _sanitize_int(val: Any) -> int | None:
    if val is None or not isinstance(val, (int, float)) or math.isnan(val):
        return None
    return int(val)


def _sanitize_list(val: Any) -> list[str] | None:
    if val is None:
        return None
    if isinstance(val, (list, tuple)):
        return [str(x) for x in val if x]
    if hasattr(val, "tolist"):
        return [str(x) for x in val.tolist() if x]
    return []


def benchmark_load_methods(
    parquet_path: str = DEFAULT_PARQUET,
    sample_size: int = 5000,
    report_path: str = BENCHMARK_REPORT,
) -> dict[str, Any]:
    """Compare performance of batched SQLAlchemy INSERTs vs. PostgreSQL COPY."""
    df = pd.read_parquet(parquet_path).head(sample_size)
    settings = get_settings()

    records = df.to_dict(orient="records")

    # Prepare product payloads
    product_rows: list[dict[str, Any]] = []
    for r in records:
        product_rows.append(
            {
                "code": str(r["code"]),
                "name": str(r["name"]),
                "brand": str(r["brand"]) if r.get("brand") else None,
                "quantity": str(r["quantity"]) if r.get("quantity") else None,
                "categories": _sanitize_list(r.get("categories_tags")),
                "ingredients_text": str(r["ingredients"]),
                "nutriscore": str(r["nutriscore_grade"]).lower()
                if r.get("nutriscore_grade")
                else None,
                "nova": _sanitize_int(r.get("nova_group")),
                "ecoscore": str(r["environmental_score_grade"]).lower()
                if r.get("environmental_score_grade")
                else None,
                "completeness": float(r["completeness"]),
                "image_path": None,
                "off_url": f"https://world.openfoodfacts.org/product/{r['code']}",
                "quality_flags": _sanitize_list(r.get("quality_flags")) or [],
                "search_text": str(r["search_text"]),
            }
        )

    # 1. Benchmark: Batched SQLAlchemy INSERT (Batch size 1,000)
    with SyncSessionLocal() as session:
        session.query(Product).delete()
        session.commit()

    start_insert = time.time()
    batch_size = 1000
    with SyncSessionLocal() as session:
        for i in range(0, len(product_rows), batch_size):
            chunk = product_rows[i : i + batch_size]
            session.execute(insert(Product), chunk)
        session.commit()
    insert_duration = time.time() - start_insert
    insert_rps = round(sample_size / insert_duration, 1)

    # 2. Benchmark: PostgreSQL COPY Protocol via psycopg
    with SyncSessionLocal() as session:
        session.query(Product).delete()
        session.commit()

    start_copy = time.time()
    conn_info = settings.sync_database_url
    with psycopg.connect(conn_info) as conn:
        with (
            conn.cursor() as cur,
            cur.copy(
                """
                COPY products (
                    code, name, brand, quantity, categories, ingredients_text,
                    nutriscore, nova, ecoscore, completeness, image_path,
                    off_url, quality_flags, search_text
                ) FROM STDIN
                """
            ) as copy,
        ):
            for row in product_rows:
                copy.write_row(
                    (
                        row["code"],
                        row["name"],
                        row["brand"],
                        row["quantity"],
                        row["categories"],
                        row["ingredients_text"],
                        row["nutriscore"],
                        row["nova"],
                        row["ecoscore"],
                        row["completeness"],
                        row["image_path"],
                        row["off_url"],
                        row["quality_flags"],
                        row["search_text"],
                    )
                )
        conn.commit()
    copy_duration = time.time() - start_copy
    copy_rps = round(sample_size / copy_duration, 1)
    speedup = round(copy_rps / insert_rps, 1) if insert_rps > 0 else 1.0

    # Write benchmark report
    report = f"""# PostgreSQL Bulk Load Benchmark Report (Phase 3)

Benchmark comparison between **Batched SQLAlchemy INSERT** and **PostgreSQL COPY** on {sample_size:,} records.

---

## Benchmark Results

| Ingestion Method | Batch Size | Duration (s) | Throughput (rows/sec) | Relative Speedup |
|---|---|---|---|---|
| **Batched SQLAlchemy INSERT** | 1,000 | {insert_duration:.3f}s | {insert_rps:,} rows/s | 1.0x (Baseline) |
| **PostgreSQL COPY (psycopg)** | Streaming | {copy_duration:.3f}s | {copy_rps:,} rows/s | **{speedup}x Faster** |

---

## Architectural Analysis

* **Why COPY is vastly superior:** The PostgreSQL `COPY` protocol operates directly over the server connection stream without generating parameterized SQL statement ASTs, eliminating statement parsing, query planning overhead, and individual round-trip acknowledgments.
* **Production Decision:** All full-dataset ingestion for LabelLens uses the streaming `COPY` protocol.
"""
    Path(report_path).parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)

    return {
        "sample_size": sample_size,
        "insert_duration": round(insert_duration, 3),
        "insert_rps": insert_rps,
        "copy_duration": round(copy_duration, 3),
        "copy_rps": copy_rps,
        "speedup": speedup,
    }


def load_clean_dataset(
    parquet_path: str = DEFAULT_PARQUET,
    clean_first: bool = True,
) -> dict[str, Any]:
    """Bulk load all clean Parquet records into PostgreSQL relational schema via COPY."""
    start_time = time.time()
    settings = get_settings()
    conn_info = settings.sync_database_url

    print("=" * 60)
    print(f"Loading clean Parquet from: {parquet_path}")
    df = pd.read_parquet(parquet_path)
    total_records = len(df)
    print(f"Loaded {total_records:,} records from Parquet. Preparing database...")

    with psycopg.connect(conn_info) as conn, conn.cursor() as cur:
        if clean_first:
            print("Clearing existing data from tables...")
            cur.execute(
                """
                TRUNCATE TABLE chat_sessions, profiles, users, product_allergens,
                product_additives, additives, diet_flags, nutrition, products CASCADE;
                """
            )
            conn.commit()

        records = df.to_dict(orient="records")

        print("1/5 Streaming 'products' table...")
        with cur.copy(
            """
            COPY products (
                code, name, brand, quantity, categories, ingredients_text,
                nutriscore, nova, ecoscore, completeness, image_path,
                off_url, quality_flags, search_text
            ) FROM STDIN
            """
        ) as copy:
            for r in records:
                code = str(r["code"])
                copy.write_row(
                    (
                        code,
                        str(r["name"]),
                        str(r["brand"]) if r.get("brand") else None,
                        str(r["quantity"]) if r.get("quantity") else None,
                        _sanitize_list(r.get("categories_tags")),
                        str(r["ingredients"]),
                        str(r["nutriscore_grade"]).lower() if r.get("nutriscore_grade") else None,
                        _sanitize_int(r.get("nova_group")),
                        str(r["environmental_score_grade"]).lower()
                        if r.get("environmental_score_grade")
                        else None,
                        float(r["completeness"]),
                        None,
                        f"https://world.openfoodfacts.org/product/{code}",
                        _sanitize_list(r.get("quality_flags")) or [],
                        str(r["search_text"]),
                    )
                )
        conn.commit()

        print("2/5 Streaming 'nutrition' table...")
        with cur.copy(
            """
            COPY nutrition (
                code, energy_kcal, fat_g, sat_fat_g, carbs_g, sugars_g,
                fiber_g, protein_g, salt_g, sodium_g
            ) FROM STDIN
            """
        ) as copy:
            for r in records:
                copy.write_row(
                    (
                        str(r["code"]),
                        _sanitize_float(r.get("energy_kcal")),
                        _sanitize_float(r.get("fat_g")),
                        _sanitize_float(r.get("sat_fat_g")),
                        _sanitize_float(r.get("carbs_g")),
                        _sanitize_float(r.get("sugars_g")),
                        None,  # fiber_g
                        _sanitize_float(r.get("protein_g")),
                        _sanitize_float(r.get("salt_g")),
                        _sanitize_float(r.get("sodium_g")),
                    )
                )
        conn.commit()

        print("3/5 Extracting & streaming 'additives' catalog and 'product_additives'...")
        unique_additives: set[str] = set()
        for r in records:
            tags = r.get("additives_tags")
            if tags is not None:
                for t in tags:
                    if t:
                        unique_additives.add(str(t).lower())

        with cur.copy("COPY additives (id, name, e_number, short_description) FROM STDIN") as copy:
            for add_id in sorted(unique_additives):
                e_num = add_id.replace("en:", "").upper()
                copy.write_row((add_id, f"Additive {e_num}", e_num, None))
        conn.commit()

        with cur.copy("COPY product_additives (code, additive_id) FROM STDIN") as copy:
            for r in records:
                code = str(r["code"])
                tags = r.get("additives_tags")
                if tags is not None:
                    for t in set(tags):
                        if t and str(t).lower() in unique_additives:
                            copy.write_row((code, str(t).lower()))
        conn.commit()

        print("4/5 Streaming 'product_allergens'...")
        with cur.copy("COPY product_allergens (code, allergen, kind) FROM STDIN") as copy:
            for r in records:
                code = str(r["code"])
                allergens = r.get("allergens_tags")
                if allergens is not None:
                    for a in set(allergens):
                        if a:
                            copy.write_row((code, str(a), "contains"))
                traces = r.get("traces_tags")
                if traces is not None:
                    for t in set(traces):
                        if t:
                            copy.write_row((code, str(t), "traces"))
        conn.commit()

        print("5/5 Streaming 'diet_flags'...")
        with cur.copy("COPY diet_flags (code, diet, value) FROM STDIN") as copy:
            for r in records:
                code = str(r["code"])
                copy.write_row((code, "vegan", str(r["diet_vegan"])))
                copy.write_row((code, "vegetarian", str(r["diet_vegetarian"])))
                copy.write_row((code, "gluten_free", str(r["diet_gluten_free"])))
                copy.write_row((code, "lactose_free", str(r["diet_lactose_free"])))
                copy.write_row((code, "palm_oil_free", str(r["diet_palm_oil_free"])))
                copy.write_row((code, "nut_free", str(r["diet_nut_free"])))
        conn.commit()

    total_time = round(time.time() - start_time, 2)
    print("=" * 60)
    print(f"Bulk load completed successfully in {total_time}s!")

    # Verify counts
    with SyncSessionLocal() as session:
        product_count = session.scalar(select(func.count(Product.code)))
        nutrition_count = session.scalar(select(func.count(Nutrition.code)))
        additive_count = session.scalar(select(func.count(Additive.id)))
        diet_count = session.scalar(select(func.count(ProductDietFlag.code)))

    print("Verified row counts in PostgreSQL:")
    print(f"- products: {product_count:,}")
    print(f"- nutrition: {nutrition_count:,}")
    print(f"- additives: {additive_count:,}")
    print(f"- diet_flags: {diet_count:,}")
    print("=" * 60)

    return {
        "products": product_count,
        "nutrition": nutrition_count,
        "additives": additive_count,
        "diet_flags": diet_count,
        "duration_seconds": total_time,
    }


if __name__ == "__main__":
    print("Running bulk load benchmarking on 5,000 products...")
    bench = benchmark_load_methods(sample_size=5000)
    print(
        f"Benchmark: Insert={bench['insert_rps']} rows/s | COPY={bench['copy_rps']} rows/s (Speedup: {bench['speedup']}x)"
    )

    print("\nRunning full clean dataset load...")
    stats = load_clean_dataset()
