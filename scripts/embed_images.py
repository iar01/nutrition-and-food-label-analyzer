import argparse

import pyarrow as pa
import pyarrow.parquet as pq
import pandas as pd
from PIL import Image
from tqdm import tqdm

from labellens.config import settings
from labellens.embeddings.image import ClipImageEmbedder

SHARD_DIR = settings.embeddings_dir / "image_clip"
SHARD_SIZE = 2048


def already_done() -> set[str]:
    done: set[str] = set()
    for f in SHARD_DIR.glob("shard_*.parquet"):
        done.update(pq.read_table(f, columns=["code"]).column("code").to_pylist())
    return done


def next_shard_index() -> int:
    ids = [int(f.stem.split("_")[1]) for f in SHARD_DIR.glob("shard_*.parquet")]
    return max(ids) + 1 if ids else 0


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--batch-size", type=int, default=64)
    args = ap.parse_args()

    SHARD_DIR.mkdir(parents=True, exist_ok=True)
    manifest = pd.read_parquet(settings.images_dir / "manifest.parquet")
    codes = manifest.loc[manifest["status"].isin(["ok", "exists"]), "code"].tolist()
    done = already_done()
    todo = [c for c in codes if c not in done]
    if args.limit:
        todo = todo[: args.limit]
    print(f"{len(done)} already embedded, {len(todo)} to do")

    embedder = ClipImageEmbedder()
    print("device:", embedder.device)
    shard_idx = next_shard_index()

    for start in range(0, len(todo), SHARD_SIZE):
        chunk = todo[start : start + SHARD_SIZE]
        out_codes: list[str] = []
        out_vecs: list[list[float]] = []

        for i in tqdm(range(0, len(chunk), args.batch_size), desc=f"shard {shard_idx}"):
            batch_codes = chunk[i : i + args.batch_size]
            images, ok_codes = [], []
            for c in batch_codes:
                try:
                    with Image.open(settings.images_dir / f"{c}.jpg") as im:
                        images.append(im.convert("RGB").copy())
                    ok_codes.append(c)
                except Exception as e:
                    print("skip", c, e)
            if not images:
                continue
            vecs = embedder.embed_images(images)
            out_codes.extend(ok_codes)
            out_vecs.extend(v.tolist() for v in vecs)

        table = pa.table({
            "code": out_codes,
            "vector": pa.array(out_vecs, type=pa.list_(pa.float32())),
        })
        pq.write_table(table, SHARD_DIR / f"shard_{shard_idx:05d}.parquet")
        shard_idx += 1


if __name__ == "__main__":
    main()