from pathlib import Path

import pyarrow.parquet as pq
from labellens.config import settings
from labellens.ids import point_id
from labellens.retrieval.qdrant_setup import get_client
from qdrant_client import models
from tqdm import tqdm

SHARD_DIR = settings.embeddings_dir / "image_clip"
BATCH = 256


def main() -> None:
    client = get_client()
    shards = sorted(Path(SHARD_DIR).glob("shard_*.parquet"))
    for shard in tqdm(shards, desc="shards"):
        rows = pq.read_table(shard).to_pylist()
        for i in range(0, len(rows), BATCH):
            chunk = rows[i : i + BATCH]
            ids = [point_id(r["code"]) for r in chunk]
            client.update_vectors(
                collection_name=settings.products_collection,
                points=[
                    models.PointVectors(id=pid, vector={"image_clip": r["vector"]})
                    for pid, r in zip(ids, chunk, strict=False)
                ],
                wait=True,
            )
            client.set_payload(
                collection_name=settings.products_collection,
                payload={"has_image": True},
                points=ids,
                wait=True,
            )


if __name__ == "__main__":
    main()
