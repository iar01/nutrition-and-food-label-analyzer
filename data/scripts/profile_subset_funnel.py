"""Calculate survival counts for Phase 1 subset rules using DuckDB."""

from pathlib import Path

import duckdb

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PARQUET_FILE = (PROJECT_ROOT / "data" / "raw" / "food.parquet").as_posix()

con = duckdb.connect()

print("Calculating raw counts and subset funnel from 4.79M products...\n")

# 1. Total products
total = con.sql(f"SELECT count(*) FROM '{PARQUET_FILE}'").fetchone()[0]
print(f"1. Total Raw Products: {total:,}")

# 2. Valid barcode length & numeric
valid_code = con.sql(f"""
    SELECT count(*) FROM '{PARQUET_FILE}'
    WHERE code IS NOT NULL
      AND regexp_matches(code, '^[0-9]{{8}}$|^[0-9]{{12}}$|^[0-9]{{13}}$|^[0-9]{{14}}$')
""").fetchone()[0]
print(
    f"2. Valid Barcode Format (8, 12, 13, 14 digits): {valid_code:,} ({valid_code / total * 100:.1f}%)"
)

# 3. Product name present
has_name = con.sql(f"""
    SELECT count(*) FROM '{PARQUET_FILE}'
    WHERE code IS NOT NULL
      AND regexp_matches(code, '^[0-9]{{8}}$|^[0-9]{{12}}$|^[0-9]{{13}}$|^[0-9]{{14}}$')
      AND len(product_name) > 0
""").fetchone()[0]
print(f"3. + Product Name Present: {has_name:,} ({has_name / total * 100:.1f}%)")

# 4. Ingredients present
has_ingredients = con.sql(f"""
    SELECT count(*) FROM '{PARQUET_FILE}'
    WHERE code IS NOT NULL
      AND regexp_matches(code, '^[0-9]{{8}}$|^[0-9]{{12}}$|^[0-9]{{13}}$|^[0-9]{{14}}$')
      AND len(product_name) > 0
      AND len(ingredients_text) > 0
""").fetchone()[0]
print(f"4. + Ingredients Present: {has_ingredients:,} ({has_ingredients / total * 100:.1f}%)")

# 5. Has images
has_image = con.sql(f"""
    SELECT count(*) FROM '{PARQUET_FILE}'
    WHERE code IS NOT NULL
      AND regexp_matches(code, '^[0-9]{{8}}$|^[0-9]{{12}}$|^[0-9]{{13}}$|^[0-9]{{14}}$')
      AND len(product_name) > 0
      AND len(ingredients_text) > 0
      AND len(images) > 0
""").fetchone()[0]
print(f"5. + Has Images: {has_image:,} ({has_image / total * 100:.1f}%)")

# 6. Has nutriments
has_nutrition = con.sql(f"""
    SELECT count(*) FROM '{PARQUET_FILE}'
    WHERE code IS NOT NULL
      AND regexp_matches(code, '^[0-9]{{8}}$|^[0-9]{{12}}$|^[0-9]{{13}}$|^[0-9]{{14}}$')
      AND len(product_name) > 0
      AND len(ingredients_text) > 0
      AND len(images) > 0
      AND len(nutriments) > 0
""").fetchone()[0]
print(f"6. + Has Nutriments List: {has_nutrition:,} ({has_nutrition / total * 100:.1f}%)")

# 7. Focus countries (e.g. en:united-states, en:united-kingdom, en:france, en:germany)
top_countries = con.sql(f"""
    SELECT list_extract(countries_tags, 1) as main_country, count(*) as count
    FROM '{PARQUET_FILE}'
    WHERE len(countries_tags) > 0
    GROUP BY main_country
    ORDER BY count DESC
    LIMIT 10
""").df()
print("\nTop 10 Countries:")
print(top_countries)

# 8. High completeness subset (completeness >= 0.5)
subset_high_quality = con.sql(f"""
    SELECT count(*) FROM '{PARQUET_FILE}'
    WHERE code IS NOT NULL
      AND regexp_matches(code, '^[0-9]{{8}}$|^[0-9]{{12}}$|^[0-9]{{13}}$|^[0-9]{{14}}$')
      AND len(product_name) > 0
      AND len(ingredients_text) > 0
      AND len(images) > 0
      AND len(nutriments) > 0
      AND completeness >= 0.5
""").fetchone()[0]
print(
    f"\n7. + Completeness >= 0.5: {subset_high_quality:,} ({subset_high_quality / total * 100:.1f}%)"
)
