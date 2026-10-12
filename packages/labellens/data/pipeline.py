"""Stage 2 & End-to-End Cleaning Pipeline (raw -> interim -> clean)."""

import time
from collections import Counter
from pathlib import Path
from typing import Any

import pandas as pd

from labellens.data.diet_rules import derive_diet_flags
from labellens.data.extract import extract_interim_subset
from labellens.data.normalizers import build_search_text, clean_ingredients_text, normalize_text
from labellens.data.schema import CleanProductsSchema
from labellens.data.validators import gs1_valid, validate_nutrition

PROJECT_ROOT = Path(__file__).resolve().parents[3]
INTERIM_PARQUET = (PROJECT_ROOT / "data" / "interim" / "products_interim.parquet").as_posix()
CLEAN_PARQUET = (PROJECT_ROOT / "data" / "clean" / "products.parquet").as_posix()
REPORT_PATH = (PROJECT_ROOT / "docs" / "data_quality_report.md").as_posix()


def clean_and_normalize_dataset(
    interim_path: str = INTERIM_PARQUET,
    clean_path: str = CLEAN_PARQUET,
    report_path: str = REPORT_PATH,
) -> dict[str, Any]:
    """Process interim Parquet into validated clean Parquet with quality report."""
    start_time = time.time()
    Path(clean_path).parent.mkdir(parents=True, exist_ok=True)
    Path(report_path).parent.mkdir(parents=True, exist_ok=True)

    # 1. Load interim records
    df = pd.read_parquet(interim_path)
    initial_count = len(df)

    # 2. Barcode GS1 Validation
    valid_mask = df["code"].apply(gs1_valid)
    invalid_barcodes_count = int((~valid_mask).sum())
    df = df[valid_mask].copy()

    # 3. Deduplication (exact barcode code & near-duplicates)
    df = df.sort_values(by="completeness", ascending=False)
    dup_codes_count = int(df.duplicated(subset=["code"]).sum())
    df = df.drop_duplicates(subset=["code"], keep="first")

    # 4. Text Normalization
    df["name"] = df["name"].apply(normalize_text)
    df["brand"] = df["brand"].apply(normalize_text)
    df["ingredients"] = df["ingredients"].apply(clean_ingredients_text)

    # Filter out empty names or ingredients after stripping tags
    non_empty_mask = (df["name"].str.len() > 0) & (df["ingredients"].str.len() > 0)
    empty_text_dropped = int((~non_empty_mask).sum())
    df = df[non_empty_mask].copy()

    # Near-duplicates deduplication: (lowercase brand, lowercase name, quantity)
    df["temp_key"] = (
        df["brand"].str.lower()
        + "||"
        + df["name"].str.lower()
        + "||"
        + df["quantity"].fillna("").str.lower()
    )
    near_dups_count = int(df.duplicated(subset=["temp_key"]).sum())
    df = df.drop_duplicates(subset=["temp_key"], keep="first").drop(columns=["temp_key"])

    # 5. Combined Single-Pass Processing (Nutrition Sanity, Diet Rules, Search Cards)
    quality_flags_counter: Counter[str] = Counter()
    quality_flags_list: list[list[str]] = []
    cleaned_nutrition_rows: list[dict[str, float | None]] = []

    vegan_flags: list[str] = []
    veg_flags: list[str] = []
    gluten_flags: list[str] = []
    lactose_flags: list[str] = []
    palm_flags: list[str] = []
    nut_flags: list[str] = []
    search_texts: list[str] = []

    records = df.to_dict(orient="records")
    for row in records:
        # Nutrition validation
        nutr_dict = {
            "energy_kcal": row.get("energy_kcal"),
            "fat_g": row.get("fat_g"),
            "sat_fat_g": row.get("sat_fat_g"),
            "carbs_g": row.get("carbs_g"),
            "sugars_g": row.get("sugars_g"),
            "protein_g": row.get("protein_g"),
            "salt_g": row.get("salt_g"),
            "sodium_g": row.get("sodium_g"),
        }
        clean_nutr, flags = validate_nutrition(nutr_dict)
        for f in flags:
            quality_flags_counter[f] += 1
        quality_flags_list.append(flags)
        cleaned_nutrition_rows.append(clean_nutr)

        # Diet classification
        tags = (
            list(row["ingredients_analysis_tags"])
            if row.get("ingredients_analysis_tags") is not None
            else []
        )
        allergens = list(row["allergens_tags"]) if row.get("allergens_tags") is not None else []
        traces = list(row["traces_tags"]) if row.get("traces_tags") is not None else []
        palm_count = row.get("ingredients_from_palm_oil_n")

        d_flags = derive_diet_flags(
            analysis_tags=tags,
            allergens=allergens,
            traces=traces,
            palm_oil_count=palm_count,
        )
        vegan_flags.append(d_flags["vegan"])
        veg_flags.append(d_flags["vegetarian"])
        gluten_flags.append(d_flags["gluten_free"])
        lactose_flags.append(d_flags["lactose_free"])
        palm_flags.append(d_flags["palm_oil_free"])
        nut_flags.append(d_flags["nut_free"])

        # Construct search card
        row.update(clean_nutr)
        search_texts.append(build_search_text(row))

    # Update dataframe with transformed fields
    nutr_df = pd.DataFrame(cleaned_nutrition_rows, index=df.index)
    for col in ["energy_kcal", "fat_g", "sat_fat_g", "carbs_g", "sugars_g", "protein_g", "salt_g"]:
        df[col] = nutr_df[col]

    df["quality_flags"] = quality_flags_list
    df["diet_vegan"] = vegan_flags
    df["diet_vegetarian"] = veg_flags
    df["diet_gluten_free"] = gluten_flags
    df["diet_lactose_free"] = lactose_flags
    df["diet_palm_oil_free"] = palm_flags
    df["diet_nut_free"] = nut_flags
    df["search_text"] = search_texts

    # 6. Pandera Schema Validation
    CleanProductsSchema.validate(df)

    # 7. Save Clean Parquet
    df.to_parquet(clean_path, index=False, compression="zstd")
    final_count = len(df)
    total_time = round(time.time() - start_time, 2)

    # 8. Generate Data Quality Report
    diet_stats = {
        "vegan": Counter(df["diet_vegan"]),
        "vegetarian": Counter(df["diet_vegetarian"]),
        "gluten_free": Counter(df["diet_gluten_free"]),
        "lactose_free": Counter(df["diet_lactose_free"]),
        "palm_oil_free": Counter(df["diet_palm_oil_free"]),
        "nut_free": Counter(df["diet_nut_free"]),
    }

    report_content = f"""# Data Quality & Cleaning Report (Phase 2)

*Automated report generated by `labellens.data.pipeline`.*

---

## 1. Pipeline Execution Summary

- **Input records (Interim):** {initial_count:,}
- **Output records (Clean):** {final_count:,}
- **Dropped Invalid Barcodes (GS1 checksum failure):** {invalid_barcodes_count:,}
- **Dropped Exact Duplicate Barcodes:** {dup_codes_count:,}
- **Dropped Near-Duplicates (same brand, title, size):** {near_dups_count:,}
- **Dropped Empty Post-Normalization Text:** {empty_text_dropped:,}
- **Processing Time:** {total_time}s
- **Output Parquet:** `{clean_path}`

---

## 2. Nutrition Quality Flags

Nutrition sanity checks identified and flagged the following anomalies without silently altering values:

| Quality Flag | Occurrences | % of Clean Records | Explanation |
|---|---|---|---|
"""
    for flag, count in quality_flags_counter.most_common():
        pct = (count / final_count) * 100
        report_content += f"| `{flag}` | {count:,} | {pct:.2f}% | Flagged in `quality_flags` |\n"

    report_content += """
---

## 3. Dietary Classification Distribution (Three-Valued Logic)

| Diet Category | 'yes' (Safe) | 'no' (Contains) | 'unknown' (Uncertain) |
|---|---|---|---|
"""
    for cat, counts in diet_stats.items():
        yes_c = counts.get("yes", 0)
        no_c = counts.get("no", 0)
        unk_c = counts.get("unknown", 0)
        report_content += f"| **{cat.replace('_', ' ').title()}** | {yes_c:,} ({yes_c / final_count * 100:.1f}%) | {no_c:,} ({no_c / final_count * 100:.1f}%) | {unk_c:,} ({unk_c / final_count * 100:.1f}%) |\n"

    report_content += """
---

## 4. Pandera Schema Validation Result

- **Validation Status:** PASSED
- **Schema:** `CleanProductsSchema`
- **Integrity Checks:** 100% unique GS1 barcodes, non-empty search cards, bounded nutritional floats, strict three-valued logic domain.
"""

    with open(report_path, "w", encoding="utf-8") as report_file:
        report_file.write(report_content)

    return {
        "initial_count": initial_count,
        "final_count": final_count,
        "invalid_barcodes": invalid_barcodes_count,
        "duplicates_removed": dup_codes_count + near_dups_count,
        "duration_seconds": total_time,
    }


def run_pipeline(force_extract: bool = False) -> dict[str, Any]:
    """Run full Phase 2 end-to-end pipeline: raw -> interim -> clean."""
    print("=" * 60)
    print("LabelLens Phase 2 Pipeline: Raw -> Interim Stage")
    print("=" * 60)
    if force_extract or not Path(INTERIM_PARQUET).exists():
        extract_stats = extract_interim_subset()
        print(
            f"-> Extracted {extract_stats['surviving_count']:,} records in {extract_stats['duration_seconds']}s"
        )
    else:
        print(f"-> Interim dataset already exists at {INTERIM_PARQUET}. Skipping extraction.")

    print("\n" + "=" * 60)
    print("LabelLens Phase 2 Pipeline: Starting Interim -> Clean Normalization")
    print("=" * 60)
    clean_stats = clean_and_normalize_dataset()
    print(
        f"-> Normalized & Validated {clean_stats['final_count']:,} records in {clean_stats['duration_seconds']}s"
    )
    print(f"-> Quality report written to {REPORT_PATH}")
    print("=" * 60)
    return clean_stats


if __name__ == "__main__":
    run_pipeline()
