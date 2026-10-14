import argparse
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

import duckdb
import httpx
import pandas as pd
from PIL import Image
from tqdm import tqdm

from labellens.config import settings
from labellens.data.image_keys import choose_key, key_prefix

BASE_URL = "https://openfoodfacts-images.s3.eu-west-3.amazonaws.com/"
MANIFEST = settings.images_dir / "manifest.parquet"


def build_plan(limit: int | None, seed: int) -> pd.DataFrame:
    codes = duckdb.sql(f"SELECT code FROM '{settings.clean_products_path}'").df()
    if limit:
        codes = codes.sample(n=min(limit, len(codes)), random_state=seed)
    codes["prefix"] = codes["code"].map(key_prefix)

    con = duckdb.connect()
    con.register("wanted", codes)
    found = con.sql(f"""
        SELECT w.code, k.key
        FROM (
            SELECT key, regexp_replace(key, '[^/]+$', '') AS prefix
            FROM read_csv('{settings.image_keys_path.as_posix()}', header=false, columns={{'key': 'VARCHAR'}})
            WHERE key LIKE '%.400.jpg'
        ) k
        JOIN wanted w ON k.prefix = w.prefix
    """).df()

    chosen = found.groupby("code")["key"].apply(lambda s: choose_key(list(s))).rename("key").reset_index()
    plan = codes[["code"]].merge(chosen, on="code", how="left")

    n_front = plan["key"].fillna("").str.contains("/front_").sum()
    n_none = plan["key"].isna().sum()
    print(f"products: {len(plan)} | front image: {n_front} | other numbered image: {len(plan) - n_front - n_none} | no image: {n_none}")
    return plan[plan["key"].notna()]


def fetch(client: httpx.Client, code: str, key: str) -> dict:
    dest = settings.images_dir / f"{code}.jpg"
    if dest.exists():
        return {"code": code, "source_key": key, "status": "exists", "bytes": dest.stat().st_size}
    for attempt in range(4):
        try:
            r = client.get(BASE_URL + key, timeout=30)
            if r.status_code == 404:
                return {"code": code, "source_key": key, "status": "missing", "bytes": 0}
            r.raise_for_status()
            tmp = dest.with_suffix(".part")
            tmp.write_bytes(r.content)
            with Image.open(tmp) as im:
                im.verify()
            tmp.replace(dest)
            return {"code": code, "source_key": key, "status": "ok", "bytes": len(r.content)}
        except Exception:
            time.sleep(2**attempt)
    return {"code": code, "source_key": key, "status": "failed", "bytes": 0}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None, help="random sample of N products (pilot run)")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args()

    settings.images_dir.mkdir(parents=True, exist_ok=True)
    plan = build_plan(args.limit, args.seed)

    results = []
    with httpx.Client(follow_redirects=True) as client, ThreadPoolExecutor(args.workers) as pool:
        futures = [pool.submit(fetch, client, r.code, r.key) for r in plan.itertuples()]
        for f in tqdm(as_completed(futures), total=len(futures), desc="downloading"):
            results.append(f.result())

    new = pd.DataFrame(results)
    new["downloaded_at"] = datetime.now(timezone.utc).isoformat()
    if MANIFEST.exists():
        new = pd.concat([pd.read_parquet(MANIFEST), new]).drop_duplicates("code", keep="last")
    new.to_parquet(MANIFEST, index=False)

    print(new["status"].value_counts().to_string())
    print(f"total on disk: {new.loc[new['status'].isin(['ok', 'exists']), 'bytes'].sum() / 1e6:.1f} MB")


if __name__ == "__main__":
    main()