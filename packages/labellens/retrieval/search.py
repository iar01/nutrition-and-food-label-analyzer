from collections.abc import Sequence
from typing import Any

from qdrant_client import QdrantClient, models

from labellens.config import settings
from labellens.embeddings.sparse import Bm25SparseEmbedder
from labellens.embeddings.text import BgeTextEmbedder
from labellens.retrieval.filters import build_filter
from labellens.retrieval.qdrant_setup import get_client


class Searcher:
    def __init__(
        self,
        client: QdrantClient | None = None,
        text_emb: BgeTextEmbedder | None = None,
        sparse_emb: Bm25SparseEmbedder | None = None,
    ) -> None:
        self.client = client or get_client()
        self.text_emb = text_emb or BgeTextEmbedder()
        self.sparse_emb = sparse_emb or Bm25SparseEmbedder()

    def products(
        self, query: str, limit: int = 5, filters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        query_filter = build_filter(filters)
        res = self.client.query_points(
            collection_name=settings.products_collection,
            prefetch=[
                models.Prefetch(
                    query=self.text_emb.embed_query(query).tolist(),
                    using="text_dense",
                    filter=query_filter,
                    limit=50,
                ),
                models.Prefetch(
                    query=self.sparse_emb.embed_query(query),
                    using="bm25",
                    filter=query_filter,
                    limit=50,
                ),
            ],
            query=models.FusionQuery(fusion=models.Fusion.RRF),
            limit=limit,
            with_payload=True,
        )
        hits: list[dict[str, Any]] = []
        for p in res.points:
            payload = p.payload or {}
            hits.append(
                {
                    "code": payload.get("code"),
                    "name": payload.get("name"),
                    "brands": payload.get("brands"),
                    "nutriscore": payload.get("nutriscore"),
                    "score": p.score,
                }
            )
        return hits

    def knowledge(
        self, query: str, k: int = 3, exclude_types: Sequence[str] = ()
    ) -> list[dict[str, Any]]:
        must_not: list[models.Condition] | None = (
            [models.FieldCondition(key="type", match=models.MatchAny(any=list(exclude_types)))]
            if exclude_types
            else None
        )
        res = self.client.query_points(
            collection_name=settings.knowledge_collection,
            query=self.text_emb.embed_query(query).tolist(),
            using="text_dense",
            query_filter=models.Filter(must_not=must_not) if must_not else None,
            limit=k,
            with_payload=True,
        )
        return [dict(p.payload or {}) for p in res.points]

    def by_image(self, vector: Sequence[float], limit: int = 5) -> list[dict[str, Any]]:
        res = self.client.query_points(
            collection_name=settings.products_collection,
            query=list(vector),
            using="image_clip",
            query_filter=models.Filter(
                must=[models.FieldCondition(key="has_image", match=models.MatchValue(value=True))]
            ),
            limit=limit,
            with_payload=True,
        )
        return [
            {
                "code": (p.payload or {}).get("code"),
                "name": (p.payload or {}).get("name"),
                "brands": (p.payload or {}).get("brands"),
                "nutriscore": (p.payload or {}).get("nutriscore"),
                "score": p.score,
            }
            for p in res.points
        ]
