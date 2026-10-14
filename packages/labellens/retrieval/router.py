import time

from PIL import Image
from qdrant_client import QdrantClient

from labellens.config import settings
from labellens.retrieval.hybrid import HybridRetriever
from labellens.retrieval.models import InputType, SearchHit, SearchResponse
from labellens.retrieval.multimodal import MultimodalRetriever
from labellens.retrieval.qdrant_setup import get_client
from labellens.retrieval.reranker import CrossEncoderReranker


class SearchEngine:
    def __init__(self, client: QdrantClient | None = None) -> None:
        self.client = client or get_client()
        self.hybrid = HybridRetriever(self.client)
        self.reranker = CrossEncoderReranker()
        self.multimodal = MultimodalRetriever(self.client)

    def search(
        self,
        query: str | None = None,
        image: Image.Image | None = None,
        diet_filters: dict[str, str] | None = None,
        use_reranker: bool = True,
        top_k: int = 10,
    ) -> SearchResponse:
        t0 = time.perf_counter()

        # Path 1: Pure Image input
        if image is not None and not query:
            hits = self.multimodal.search_by_image(image, limit=top_k)
            latency = (time.perf_counter() - t0) * 1000
            return SearchResponse(
                query="[image_upload]",
                input_type=InputType.PRODUCT_IMAGE,
                hits=hits,
                total_found=len(hits),
                latency_ms=round(latency, 2),
            )

        # Path 2: Text input
        clean_q = (query or "").strip()

        # 2a: Barcode input (exact numeric digits)
        if clean_q.isdigit() and len(clean_q) in (8, 12, 13, 14):
            # Barcode check directly against Qdrant payload or Postgres
            res = self.client.scroll(
                collection_name=settings.products_collection,
                scroll_filter=self.hybrid.build_diet_filter({"code": clean_q}),
                limit=1,
                with_payload=True,
            )[0]
            if res:
                p = res[0].payload or {}
                hit = SearchHit(
                    id=str(res[0].id),
                    code=clean_q,
                    name=str(p.get("name", "")),
                    brand=p.get("brand") or p.get("brands"),
                    score=1.0,
                    rank=1,
                    match_source="barcode_exact",
                    payload=p,
                )
                latency = (time.perf_counter() - t0) * 1000
                return SearchResponse(
                    query=clean_q,
                    input_type=InputType.BARCODE,
                    hits=[hit],
                    total_found=1,
                    latency_ms=round(latency, 2),
                )

        # 2b: Standard Text Query (Hybrid RRF -> Rerank)
        candidates = self.hybrid.search(
            query=clean_q,
            limit=top_k * 2 if use_reranker else top_k,
            diet_filters=diet_filters,
        )

        if use_reranker and candidates:
            final_hits = self.reranker.rerank(clean_q, candidates, top_k=top_k)
        else:
            final_hits = candidates[:top_k]

        latency = (time.perf_counter() - t0) * 1000
        return SearchResponse(
            query=clean_q,
            input_type=InputType.TEXT,
            hits=final_hits,
            total_found=len(final_hits),
            latency_ms=round(latency, 2),
            filters_applied=diet_filters,
        )
