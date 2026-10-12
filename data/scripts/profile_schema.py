"""Profile schema and column names in food.parquet."""

from pathlib import Path

import duckdb

PROJECT_ROOT = Path(__file__).resolve().parents[2]
PARQUET_FILE = (PROJECT_ROOT / "data" / "raw" / "food.parquet").as_posix()

con = duckdb.connect()

# 1. Fetch column schema
columns = con.sql(f"DESCRIBE SELECT * FROM '{PARQUET_FILE}'").fetchall()
col_info = [{"name": c[0], "type": c[1]} for c in columns]

print(f"Total columns: {len(col_info)}")
print("--- Column Sample (First 30) ---")
for c in col_info[:30]:
    print(f"  {c['name']}: {c['type']}")

# Find key nutrition and metadata columns
print("\n--- Key Metadata Columns Found ---")
key_terms = ["code", "product_name", "brands", "categories", "ingredients", "nutriment", "nutriscore", "nova", "ecoscore", "countries", "image", "completeness"]
found = [c for c in col_info if any(k in c["name"].lower() for k in key_terms)]
for f in found:
    print(f"  {f['name']}: {f['type']}")
