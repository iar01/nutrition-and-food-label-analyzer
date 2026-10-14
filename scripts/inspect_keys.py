import duckdb
from labellens.config import settings
from labellens.data.image_keys import key_prefix

codes = (
    duckdb.sql(f"SELECT code FROM '{settings.clean_products_path}' USING SAMPLE 8")
    .df()["code"]
    .tolist()
)
prefixes = {key_prefix(c): c for c in codes}
in_list = ", ".join(f"'{p}'" for p in prefixes)

rows = duckdb.sql(f"""
    SELECT key
    FROM read_csv('{settings.image_keys_path.as_posix()}', header=false, columns={{'key': 'VARCHAR'}})
    WHERE regexp_replace(key, '[^/]+$', '') IN ({in_list})
    ORDER BY key
""").fetchall()

found = {}
for (key,) in rows:
    found.setdefault(key.rsplit("/", 1)[0] + "/", []).append(key.rsplit("/", 1)[1])

for prefix, code in prefixes.items():
    print(f"\n{code}  ->  {prefix}")
    for name in found.get(
        prefix, ["(NO KEYS FOUND, my prefix rule may be wrong for this barcode)"]
    ):
        print("   ", name)
