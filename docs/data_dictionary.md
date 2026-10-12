# LabelLens Data Dictionary

This document details the schema, data types, nested structures, and usage of the columns extracted from the Open Food Facts Parquet export (`food.parquet`).

---

## 1. Dataset Overview

- **Source File:** `data/raw/food.parquet` (Hugging Face `openfoodfacts/product-database`)
- **Total Records:** 4,792,125
- **Total Raw Columns:** 111
- **File Format:** Apache Parquet (Snappy compressed)
- **License:** Open Database License (ODbL) 1.0; Images under CC BY-SA.

---

## 2. Core Columns Specification

| Column | Raw Parquet Type | Clean Target Type | Description & Purpose |
|---|---|---|---|
| `code` | `VARCHAR` | `VARCHAR(32)` | Product barcode (EAN-13, EAN-8, UPC-A, GTIN-14). Primary key for exact lookups. |
| `product_name` | `STRUCT(lang VARCHAR, text VARCHAR)[]` | `VARCHAR` | Nested list of localized product names. In Phase 2, flattened preferring English (`en`) or the dominant language. |
| `brands` | `VARCHAR` | `VARCHAR` | Brand name or comma-separated list of brands (e.g. "Nestlé", "Oatly"). |
| `brands_tags` | `VARCHAR[]` | `VARCHAR[]` | Normalized lowercase brand identifier tags. |
| `categories` | `VARCHAR` | `VARCHAR` | Comma-separated category hierarchy string. |
| `categories_tags` | `VARCHAR[]` | `VARCHAR[]` | Normalized category tags (e.g. `['en:beverages', 'en:plant-based-foods']`). Used for alternatives search and filtering. |
| `ingredients_text` | `STRUCT(lang VARCHAR, text VARCHAR)[]` | `VARCHAR` | Raw ingredient list string per language. Extracted and normalized in cleaning pipeline. |
| `ingredients_analysis_tags` | `VARCHAR[]` | `VARCHAR[]` | Automated tags for dietary classification: `en:vegan`, `en:non-vegan`, `en:vegetarian`, `en:palm-oil-free`, `en:palm-oil`. |
| `allergens_tags` | `VARCHAR[]` | `VARCHAR[]` | Standardized allergen tags present in product (e.g. `en:gluten`, `en:milk`, `en:soybeans`, `en:nuts`). |
| `traces_tags` | `VARCHAR[]` | `VARCHAR[]` | Cross-contamination and manufacturing trace warnings (e.g. `en:peanuts`, `en:celery`). |
| `additives_tags` | `VARCHAR[]` | `VARCHAR[]` | Detected food additives listed as E-number tags (e.g. `en:e322`, `en:e330`, `en:e471`). |
| `nutriments` | `STRUCT(name, value, 100g, serving, unit...)[]` | Normalized table / `STRUCT` | Array of macro and micronutrients. We extract per-100g values for: energy (kcal), fat, saturated fat, carbs, sugars, fiber, protein, salt. |
| `nutriscore_grade` | `VARCHAR` | `VARCHAR(1)` | Nutri-Score nutritional quality rating: `a`, `b`, `c`, `d`, `e`. |
| `nutriscore_score` | `INTEGER` | `INTEGER` | Raw numeric Nutri-Score calculation (-15 to 40). |
| `nova_group` | `INTEGER` | `INTEGER` | NOVA ultra-processing degree classification (1: unprocessed, 2: processed culinary ingredients, 3: processed, 4: ultra-processed). |
| `environmental_score_grade` | `VARCHAR` | `VARCHAR(1)` | Eco-Score / Green impact rating (`a` to `e`). |
| `quantity` | `VARCHAR` | `VARCHAR` | Net weight / volume packaging string (e.g. "500 g", "1 L"). |
| `images` | `STRUCT(key, imgid, rev, sizes...)[]` | `VARCHAR` (URL) | Array of uploaded product images. Used to resolve the front packaging image at ~400px resolution. |
| `completeness` | `FLOAT` | `FLOAT` | Open Food Facts data completeness index ranging from `0.0` (bare scan) to `1.0` (fully audited). |
| `countries_tags` | `VARCHAR[]` | `VARCHAR[]` | Countries where the product is sold (e.g. `['en:united-states', 'en:france']`). Used for regional subset filtering. |

---

## 3. Nested Structures Details

### 3.1 `product_name` & `ingredients_text`
Both fields are stored in raw Parquet as lists of structs:
```text
STRUCT(lang VARCHAR, text VARCHAR)[]
```
- **Example:** `[{'lang': 'en', 'text': 'Rolled Oats'}, {'lang': 'fr', 'text': 'Flocons d avoine'}]`
- **Cleaning Strategy:** 
  1. Inspect array for `lang = 'en'`.
  2. If absent, fallback to `main_languages_tags` or first non-empty text.
  3. Strip HTML markup, excess whitespace, and normalize Unicode NFKC.

### 3.2 `nutriments`
Nutriments are represented as an array of structs:
```text
STRUCT(
  name VARCHAR,
  value FLOAT,
  "100g" FLOAT,
  serving FLOAT,
  unit VARCHAR,
  prepared_value FLOAT,
  prepared_100g FLOAT,
  prepared_serving FLOAT,
  prepared_unit VARCHAR
)[]
```
- **Extraction Strategy:** Per-100g standard (`"100g"` field) extracted into dedicated relational columns in PostgreSQL (`energy_kcal`, `fat_g`, `sat_fat_g`, `carbs_g`, `sugars_g`, `fiber_g`, `protein_g`, `salt_g`).

### 3.3 `images`
```text
STRUCT(
  key VARCHAR,
  imgid INTEGER,
  rev INTEGER,
  sizes STRUCT(
    "100" STRUCT(h INTEGER, w INTEGER),
    "200" STRUCT(h INTEGER, w INTEGER),
    "400" STRUCT(h INTEGER, w INTEGER),
    "full" STRUCT(h INTEGER, w INTEGER)
  ),
  uploaded_t BIGINT,
  uploader VARCHAR
)[]
```
- **Front Image Selection:** Find entries where `key` matches `'front'` or `'front_en'` and extract URL for the `400` size.
