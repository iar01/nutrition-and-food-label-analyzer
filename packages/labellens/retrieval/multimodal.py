from PIL import Image
from qdrant_client import QdrantClient

from labellens.config import settings
from labellens.embeddings.image import ClipImageEmbedder
from labellens.retrieval.models import SearchHit


class MultimodalRetriever:
    def __init__(self, client: QdrantClient, collection_name: str | None = None) -> None:
        self.client = client
        self.collection_name = collection_name or settings.products_collection
        self.clip = ClipImageEmbedder()

    def search_by_image(self, image: Image.Image, limit: int = 10) -> list[SearchHit]:
        """Search products using an uploaded product photo."""
        vec = self.clip.embed_images([image])[0].tolist()

        res = self.client.query_points(
            collection_name=self.collection_name,
            query=vec,
            using="image_clip",
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
                    score=float(point.score or 0.0),
                    rank=i + 1,
                    match_source="clip_visual",
                    payload=p,
                )
            )
        return hits
