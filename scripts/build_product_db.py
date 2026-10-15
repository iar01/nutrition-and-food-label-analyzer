from pathlib import Path

import duckdb
from labellens.config import settings

settings.product_db_path.parent.mkdir(parents=True, exist_ok=True)
con = duckdb.connect(str(settings.product_db_path))
parquet = Path(settings.clean_products_path).as_posix()
con.execute(f"CREATE OR REPLACE TABLE products AS SELECT * FROM read_parquet('{parquet}')")
con.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_products_code ON products(code)")
print("rows:", con.execute("SELECT count(*) FROM products").fetchone())
con.close()
