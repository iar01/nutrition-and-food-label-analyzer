"""Pandera schema validation for clean product dataset."""

import pandera.pandas as pa
from pandera.pandas import Check, Column

# Allowed three-valued logic domain for dietary flags
DIET_VALUES = ["yes", "no", "unknown"]

CleanProductsSchema = pa.DataFrameSchema(
    columns={
        "code": Column(
            pa.String,
            checks=[
                Check.str_length(min_value=8, max_value=14),
                Check.str_matches(r"^[0-9]+$"),
            ],
            nullable=False,
            unique=True,
            description="GS1 validated product barcode",
        ),
        "name": Column(
            pa.String,
            checks=[Check.str_length(min_value=1)],
            nullable=False,
            description="Normalized product title",
        ),
        "brand": Column(pa.String, nullable=True),
        "ingredients": Column(
            pa.String,
            checks=[Check.str_length(min_value=1)],
            nullable=False,
            description="Cleaned ingredient list text",
        ),
        "energy_kcal": Column(pa.Float, checks=[Check.in_range(0.0, 1000.0)], nullable=True),
        "fat_g": Column(pa.Float, checks=[Check.in_range(0.0, 100.0)], nullable=True),
        "sat_fat_g": Column(pa.Float, checks=[Check.in_range(0.0, 100.0)], nullable=True),
        "carbs_g": Column(pa.Float, checks=[Check.in_range(0.0, 100.0)], nullable=True),
        "sugars_g": Column(pa.Float, checks=[Check.in_range(0.0, 100.0)], nullable=True),
        "protein_g": Column(pa.Float, checks=[Check.in_range(0.0, 100.0)], nullable=True),
        "salt_g": Column(pa.Float, checks=[Check.in_range(0.0, 100.0)], nullable=True),
        "diet_vegan": Column(pa.String, checks=[Check.isin(DIET_VALUES)], nullable=False),
        "diet_vegetarian": Column(pa.String, checks=[Check.isin(DIET_VALUES)], nullable=False),
        "diet_gluten_free": Column(pa.String, checks=[Check.isin(DIET_VALUES)], nullable=False),
        "diet_lactose_free": Column(pa.String, checks=[Check.isin(DIET_VALUES)], nullable=False),
        "diet_palm_oil_free": Column(pa.String, checks=[Check.isin(DIET_VALUES)], nullable=False),
        "diet_nut_free": Column(pa.String, checks=[Check.isin(DIET_VALUES)], nullable=False),
        "completeness": Column(pa.Float, checks=[Check.in_range(0.0, 2.0)], nullable=False),
        "search_text": Column(pa.String, checks=[Check.str_length(min_value=10)], nullable=False),
    },
    coerce=True,
    strict=False,
)
