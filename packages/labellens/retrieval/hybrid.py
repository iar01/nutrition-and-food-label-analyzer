from qdrant_client import QdrantClient, models

from labellens.config import settings
from labellens.embeddings.sparse import Bm25SparseEmbedder
from labellens.embeddings.text import BgeTextEmbedder
from labellens.retrieval.models import SearchHit


class HybridRetriever:
    def __init__(
        self,
        client: QdrantClient,
        collection_name: str | None = None,
        text_embedder: BgeTextEmbedder | None = None,
        sparse_embedder: Bm25SparseEmbedder | None = None,
    ) -> None:
        self.client = client
        self.collection_name = collection_name or settings.products_collection
        self.text_emb = text_embedder or BgeTextEmbedder()
        self.sparse_emb = sparse_embedder or Bm25SparseEmbedder()

    def build_diet_filter(self, diets: dict[str, str] | None) -> models.Filter | None:
        """Translate user dietary requirements (e.g. {'diet_vegan': 'yes'}) into Qdrant filters."""
        if not diets:
            return None
        conditions: list[models.Condition] = [
            models.FieldCondition(key=k, match=models.MatchValue(value=v)) for k, v in diets.items()
        ]
        return models.Filter(must=conditions)

    def search(
        self,
        query: str,
        limit: int = 20,
        prefetch_limit: int = 50,
        diet_filters: dict[str, str] | None = None,
    ) -> list[SearchHit]:
        """Execute server-side hybrid prefetching fused via Reciprocal Rank Fusion."""
        dense_vector = self.text_emb.embed_query(query).tolist()
        sparse_vector = self.sparse_emb.embed_query(query)
        qdrant_filter = self.build_diet_filter(diet_filters)

        # Server-side parallel prefetch & RRF fusion
        res = self.client.query_points(
            collection_name=self.collection_name,
            prefetch=[
                models.Prefetch(
                    query=dense_vector,
                    using="text_dense",
                    limit=prefetch_limit,
                    filter=qdrant_filter,
                ),
                models.Prefetch(
                    query=sparse_vector,
                    using="bm25",
                    limit=prefetch_limit,
                    filter=qdrant_filter,
                ),
            ],
            query=models.FusionQuery(fusion=models.Fusion.RRF),
            limit=limit,
            with_payload=True,
        )

        hits = []
        for i, point in enumerate(res.points):
            p = point.payload or {}
            hits.append(
                SearchHit(
                    id=str(point.id),
                    code=str(p.get("code", "")),
                    name=str(p.get("name", "Unknown")),
                    brand=p.get("brand") or p.get("brands"),
                    score=float(point.score if point.score is not None else 0.0),
                    rank=i + 1,
                    match_source="hybrid_rrf",
                    payload=p,
                )
            )
        return hits
