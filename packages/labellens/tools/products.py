import math
from pathlib import Path
from typing import Any

import duckdb
from labellens.config import settings


def _clean(value: Any) -> Any:
    """DuckDB gives None for NULL, but NaN floats can still sneak in. JSON hates NaN."""
    if isinstance(value, float) and math.isnan(value):
        return None
    return value


class ProductRepo:
    def __init__(self, db_path: Path | None = None) -> None:
        self.con = duckdb.connect(str(db_path or settings.product_db_path), read_only=True)

    def get(self, code: str) -> dict[str, Any] | None:
        cur = self.con.execute("SELECT * FROM products WHERE code = ?", [code])
        row = cur.fetchone()
        if row is None:
            return None
        columns = [d[0] for d in cur.description]
        return {col: _clean(val) for col, val in zip(columns, row, strict=False)}
