"""Stage 1: Extract candidate subset from raw food.parquet to interim.parquet."""

import time
from pathlib import Path

import duckdb

PROJECT_ROOT = Path(__file__).resolve().parents[3]
RAW_PARQUET = (PROJECT_ROOT / "data" / "raw" / "food.parquet").as_posix()
INTERIM_PARQUET = (PROJECT_ROOT / "data" / "interim" / "products_interim.parquet").as_posix()


def extract_interim_subset(
    raw_path: str = RAW_PARQUET,
    interim_path: str = INTERIM_PARQUET,
    completeness_threshold: float = 0.5,
    row_limit: int | None = 200000,
) -> dict[str, int | float]:
    """Extract, flatten, and filter subset from raw Open Food Facts Parquet.

    Uses DuckDB to unnest structures in-place and write to interim Parquet without
    loading the 8 GB file into Python RAM.
    """
    start_time = time.time()
    con = duckdb.connect()

    # Ensure parent directory exists
    Path(interim_path).parent.mkdir(parents=True, exist_ok=True)

    limit_clause = f"LIMIT {row_limit}" if row_limit else ""

    extract_query = f"""
    COPY (
        SELECT
            code,
            COALESCE(
                list_filter(product_name, x -> x.lang = 'en')[1]."text",
                product_name[1]."text"
            ) AS name,
            brands AS brand,
            quantity,
            COALESCE(
                list_filter(ingredients_text, x -> x.lang = 'en')[1]."text",
                ingredients_text[1]."text"
            ) AS ingredients,
            list_filter(nutriments, x -> x."name" = 'energy-kcal')[1]."100g" AS energy_kcal,
            list_filter(nutriments, x -> x."name" = 'fat')[1]."100g" AS fat_g,
            list_filter(nutriments, x -> x."name" = 'saturated-fat')[1]."100g" AS sat_fat_g,
            list_filter(nutriments, x -> x."name" = 'carbohydrates')[1]."100g" AS carbs_g,
            list_filter(nutriments, x -> x."name" = 'sugars')[1]."100g" AS sugars_g,
            list_filter(nutriments, x -> x."name" = 'proteins')[1]."100g" AS protein_g,
            list_filter(nutriments, x -> x."name" = 'salt')[1]."100g" AS salt_g,
            list_filter(nutriments, x -> x."name" = 'sodium')[1]."100g" AS sodium_g,
            nutriscore_grade,
            nova_group,
            environmental_score_grade,
            completeness,
            categories_tags,
            allergens_tags,
            traces_tags,
            additives_tags,
            ingredients_analysis_tags,
            ingredients_from_palm_oil_n
        FROM '{raw_path}'
        WHERE code IS NOT NULL
          AND regexp_matches(code, '^[0-9]{{8}}$|^[0-9]{{12}}$|^[0-9]{{13}}$|^[0-9]{{14}}$')
          AND len(product_name) > 0
          AND len(ingredients_text) > 0
          AND len(images) > 0
          AND len(nutriments) > 0
          AND completeness >= {completeness_threshold}
        ORDER BY completeness DESC
        {limit_clause}
    ) TO '{interim_path}' (FORMAT PARQUET, COMPRESSION ZSTD);
    """

    con.sql(extract_query)

    count_result = con.sql(f"SELECT count(*) FROM '{interim_path}'").fetchone()
    surviving_count = count_result[0] if count_result else 0
    duration = time.time() - start_time

    return {
        "surviving_count": surviving_count,
        "duration_seconds": round(duration, 2),
    }


if __name__ == "__main__":
    print(f"Extracting interim dataset to: {INTERIM_PARQUET}...")
    stats = extract_interim_subset()
    print(f"Extracted {stats['surviving_count']:,} records in {stats['duration_seconds']}s")
