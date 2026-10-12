import io
import sys
from pathlib import Path

import duckdb

# Ensure UTF-8 output on Windows consoles for DuckDB table rendering
if sys.platform == "win32" and isinstance(sys.stdout, io.TextIOWrapper):
    sys.stdout.reconfigure(encoding="utf-8")

# Dynamically resolve path to project root regardless of where script is executed from
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PARQUET_FILE = (PROJECT_ROOT / "data" / "raw" / "food.parquet").as_posix()

con = duckdb.connect()
con.sql(f"DESCRIBE SELECT * FROM '{PARQUET_FILE}'").show()
con.sql(f"""
  SELECT count(*) AS total,
         count(product_name) AS has_name,
         count(ingredients_text) AS has_ingredients
  FROM '{PARQUET_FILE}'
""").show()
