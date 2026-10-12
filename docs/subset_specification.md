# LabelLens Dataset Subset Specification

*Documenting the filtering funnel, survival counts, subset rules, and capacity checks for Phase 1.*

---

## 1. Motivation & Free-Tier Capacity Constraints

The raw Open Food Facts database contains **4,792,125 products** (7.91 GB compressed Parquet). 

Embedding all 4.8 million products across text (384-d), CLIP image (512-d), and sparse BM25 vectors would require over **18 GB of RAM/VRAM** for embeddings and vector indices alone, exceeding free-tier hosting limits (Qdrant Cloud free tier cap ~1 GB, free VPS ~2 GB).

Therefore, Phase 1 establishes a **curated subset target of ~150,000–250,000 products**:
- Retains maximum data richness and zero quality drop.
- 100% of products have valid barcodes, readable ingredient lists, complete nutrition facts, and front packaging images.
- Easily fits in free-tier vector database memory with scalar quantization (~360 MB vector footprint).

---

## 2. Subset Filtering Funnel (Measured on `food.parquet`)

The following funnel was computed directly using DuckDB against `data/raw/food.parquet`:

| Step | Filter Rule | Surviving Rows | % of Total | Drop from Previous | Reason & Impact |
|---|---|---|---|---|---|
| **0** | **Total Raw Export** | **4,792,125** | 100.0% | — | Baseline raw Parquet export. |
| **1** | **Valid Barcode Format** | **4,721,147** | 98.5% | -70,978 (-1.5%) | Excludes non-standard, internal, or malformed barcodes (must be 8, 12, 13, or 14 digits). |
| **2** | **Product Name Present** | **4,440,824** | 92.7% | -280,323 (-5.8%) | Excludes orphaned barcode records with zero name text. |
| **3** | **Ingredients Present** | **1,253,334** | **26.2%** | **-3,187,490 (-66.5%)** | **RULE THAT REMOVES THE MOST.** Crowd-sourced scans frequently lack ingredient transcription. |
| **4** | **Packaging Images Present** | **964,661** | 20.1% | -288,673 (-6.1%) | Must have at least one uploaded packaging photo. |
| **5** | **Nutriments List Present** | **964,178** | 20.1% | -483 (<0.1%) | Products with ingredients and images almost always have nutriments recorded. |
| **6** | **High Completeness (`completeness >= 0.5`)** | **822,425** | 17.2% | -141,753 (-2.9%) | Keeps products with at least 50% data verification. |
| **7** | **Target Language / Country Focus** (US, UK, CA, AU, FR) | **~250,000** | ~5.2% | -572,425 (-12.0%) | Focuses on English packaging + top European markets. |
| **Final** | **Curated Production Subset** | **150,000 – 200,000** | **~4.0%** | — | Top completeness items matching all criteria. |

---

## 3. Analysis: Which Rule Removes the Most?

> **Rule 3 (Ingredients Present) removes by far the most records: 3,187,490 products (66.5% of the entire database).**

### Why?
Open Food Facts is a crowdsourced community project. Mobile app users frequently scan barcodes in supermarkets and quickly enter the product title or brand, but do not take the time to photograph the back panel or transcribe lengthy ingredient lists. For LabelLens (where additive explanation, allergen checking, and diet verification are the primary purpose), products without ingredients cannot be analyzed and are safely filtered out.

---

## 4. Subset Extraction Rule for Phase 2 Pipeline

A product is included in `data/clean/products.parquet` if and only if:
1. `code` passes GS1 checksum validation (8, 12, 13, or 14 digits).
2. `product_name` is non-empty.
3. `ingredients_text` is non-empty.
4. Core macronutrients per 100g are present: `energy_kcal`, `fat`, `saturated_fat`, `carbohydrates`, `sugars`, `protein`, `salt`.
5. At least one front packaging image exists in `images`.
6. Sorted by `completeness DESC` and capped at 200,000 records.
