"""Test unpacking nested columns from food.parquet."""

from pathlib import Path

import duckdb

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PARQUET_FILE = (PROJECT_ROOT / "data" / "raw" / "food.parquet").as_posix()

con = duckdb.connect()

# Test extracting english or first text from product_name and ingredients_text
# In DuckDB, product_name is STRUCT(lang VARCHAR, "text" VARCHAR)[]
query = f"""
SELECT
    code,
    COALESCE(
        list_filter(product_name, x -> x.lang = 'en')[1]."text",
        product_name[1]."text"
    ) AS name,
    COALESCE(
        list_filter(ingredients_text, x -> x.lang = 'en')[1]."text",
        ingredients_text[1]."text"
    ) AS ingredients,
    list_filter(nutriments, x -> x."name" = 'energy-kcal')[1]."100g" AS energy_kcal,
    list_filter(nutriments, x -> x."name" = 'fat')[1]."100g" AS fat_100g,
    list_filter(nutriments, x -> x."name" = 'saturated-fat')[1]."100g" AS sat_fat_100g,
    list_filter(nutriments, x -> x."name" = 'carbohydrates')[1]."100g" AS carbs_100g,
    list_filter(nutriments, x -> x."name" = 'sugars')[1]."100g" AS sugars_100g,
    list_filter(nutriments, x -> x."name" = 'proteins')[1]."100g" AS protein_100g,
    list_filter(nutriments, x -> x."name" = 'salt')[1]."100g" AS salt_100g,
    list_filter(nutriments, x -> x."name" = 'sodium')[1]."100g" AS sodium_100g,
    nutriscore_grade,
    nova_group,
    environmental_score_grade,
    completeness,
    categories_tags,
    allergens_tags,
    traces_tags,
    additives_tags,
    ingredients_analysis_tags
FROM '{PARQUET_FILE}'
WHERE len(product_name) > 0
  AND len(ingredients_text) > 0
  AND len(nutriments) > 0
LIMIT 5
"""

res = con.sql(query).df()
print(res.to_dict(orient="records")[0])
