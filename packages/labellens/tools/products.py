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
        cur = self.con.cursor()  # a private connection per call: safe across threads
        try:
            result = cur.execute("SELECT * FROM products WHERE code = ?", [code])
            row = result.fetchone()
            if row is None:
                return None
            columns = [d[0] for d in result.description]
        finally:
            cur.close()
        return {col: _clean(val) for col, val in zip(columns, row, strict=False)}

    def ping(self) -> bool:
        cur = self.con.cursor()
        try:
            return cur.execute("SELECT 1").fetchone() == (1,)
        finally:
            cur.close()
