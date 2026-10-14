import argparse
import uuid
from pathlib import Path
from typing import Any

import yaml
from labellens.config import settings
from labellens.embeddings.text import BgeTextEmbedder
from labellens.knowledge.chunking import chunk_words
from labellens.retrieval.qdrant_setup import create_knowledge_collection, get_client
from qdrant_client import models
from tqdm import tqdm

KNOWLEDGE_DIR = Path("docs/knowledge")
EXTRA_FIELDS = ("e_number", "category", "vegan")
BATCH = 64


def load_cards() -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for path in sorted(KNOWLEDGE_DIR.glob("*.yaml")):
        cards.extend(yaml.safe_load(path.read_text(encoding="utf-8")) or [])
    return cards


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--recreate",
        action="store_true",
        help="delete and recreate the collection (use after changing payload indexes)",
    )
    args = ap.parse_args()

    client = get_client()
    emb = BgeTextEmbedder()
    create_knowledge_collection(client, text_dim=emb.dim, recreate=args.recreate)

    items: list[tuple[str, str, dict[str, Any]]] = []  # (point id, text to embed, payload)
    for card in load_cards():
        for i, chunk in enumerate(chunk_words(card["text"])):
            payload: dict[str, Any] = {
                "key": card["key"],
                "type": card["type"],
                "title": card["title"],
                "text": chunk,
                "source_url": card.get("source_url", ""),
            }
            for field in EXTRA_FIELDS:
                if field in card:
                    payload[field] = card[field]
            point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"labellens:knowledge:{card['key']}:{i}"))
            items.append((point_id, f"{card['title']}. {chunk}", payload))

    for start in tqdm(range(0, len(items), BATCH), desc="knowledge"):
        batch = items[start : start + BATCH]
        vectors = emb.embed_documents([doc for _, doc, _ in batch])
        points = [
            models.PointStruct(
                id=pid,
                vector={"text_dense": vectors[i].tolist()},
                payload=payload,
            )
            for i, (pid, _, payload) in enumerate(batch)
        ]
        client.upsert(settings.knowledge_collection, points=points, wait=True)

    print("knowledge points:", client.count(settings.knowledge_collection, exact=True).count)


if __name__ == "__main__":
    main()
