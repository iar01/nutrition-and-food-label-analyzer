"""Validation rules for product barcodes and nutritional sanity."""


def gs1_valid(code: str) -> bool:
    """Validate barcode using GS1 modulo-10 checksum algorithm.

    Accepts standard GS1 lengths: GTIN-8 (8), UPC-A (12), EAN-13 (13), and GTIN-14 (14).
    """
    if not code or not isinstance(code, str):
        return False

    clean_code = code.strip()
    if not clean_code.isdigit() or len(clean_code) not in (8, 12, 13, 14):
        return False

    digits = [int(c) for c in clean_code]
    check = digits.pop()
    total = sum(d * (3 if i % 2 == 0 else 1) for i, d in enumerate(reversed(digits)))
    return (10 - total % 10) % 10 == check


def validate_nutrition(
    nutrition: dict[str, float | None],
) -> tuple[dict[str, float | None], list[str]]:
    """Apply nutritional sanity checks on per-100g values.

    Never silently corrects values. Records detected anomalies in `quality_flags`.

    Sanity rules:
    - Macros must be between 0g and 100g.
    - Saturated fat must not exceed total fat.
    - Sugars must not exceed total carbohydrates.
    - Salt vs Sodium ratio check: salt is approximately 2.54 * sodium.
    - Total macro sum (fat + carbs + protein + fiber + salt) should not exceed 105g.
    - Calories calculation: 4*protein + 4*carbs + 9*fat should roughly align with energy_kcal.
    """
    flags: list[str] = []
    clean: dict[str, float | None] = dict(nutrition)

    energy = clean.get("energy_kcal")
    fat = clean.get("fat_g")
    sat_fat = clean.get("sat_fat_g")
    carbs = clean.get("carbs_g")
    sugars = clean.get("sugars_g")
    fiber = clean.get("fiber_g")
    protein = clean.get("protein_g")
    salt = clean.get("salt_g")
    sodium = clean.get("sodium_g")

    # 1. Bounds check (0 - 100g for gram-based nutrients)
    macro_fields = [
        ("fat_g", fat),
        ("sat_fat_g", sat_fat),
        ("carbs_g", carbs),
        ("sugars_g", sugars),
        ("fiber_g", fiber),
        ("protein_g", protein),
        ("salt_g", salt),
    ]

    for field_name, val in macro_fields:
        if val is not None:
            if val < 0.0:
                flags.append(f"{field_name}_negative")
                clean[field_name] = None
            elif val > 100.0:
                flags.append(f"{field_name}_exceeds_100g")
                clean[field_name] = None

    # Re-fetch cleaned values for relational checks
    fat = clean.get("fat_g")
    sat_fat = clean.get("sat_fat_g")
    carbs = clean.get("carbs_g")
    sugars = clean.get("sugars_g")
    protein = clean.get("protein_g")
    salt = clean.get("salt_g")

    # 2. Saturated fat <= total fat
    if (
        fat is not None and sat_fat is not None and sat_fat > fat + 0.1
    ):  # Allow 0.1g margin for rounding
        flags.append("sat_fat_exceeds_total_fat")

    # 3. Sugars <= total carbohydrates
    if carbs is not None and sugars is not None and sugars > carbs + 0.1:
        flags.append("sugars_exceed_carbs")

    # 4. Salt vs Sodium check (~2.54 ratio)
    if salt is not None and sodium is not None and sodium > 0.05:
        expected_salt = sodium * 2.54
        if abs(salt - expected_salt) > 1.0:  # Allow reasonable labeling variance
            flags.append("salt_sodium_discrepancy")

    # 5. Macro sum sanity (< 105g)
    macro_sum = (fat or 0.0) + (carbs or 0.0) + (protein or 0.0) + (fiber or 0.0) + (salt or 0.0)
    if macro_sum > 105.0:
        flags.append("macro_sum_exceeds_100g")

    # 6. Calorie estimate sanity check (energy_kcal should be plausible)
    if energy is not None:
        if energy < 0.0:
            flags.append("energy_kcal_negative")
            clean["energy_kcal"] = None
        elif energy > 900.0:  # Pure fat is ~900 kcal/100g
            flags.append("energy_kcal_exceeds_max")
            clean["energy_kcal"] = None
        elif fat is not None and carbs is not None and protein is not None:
            calc_kcal = (carbs * 4.0) + (protein * 4.0) + (fat * 9.0)
            if abs(energy - calc_kcal) > 300.0:  # Discrepancy threshold
                flags.append("energy_macro_discrepancy")

    return clean, flags
