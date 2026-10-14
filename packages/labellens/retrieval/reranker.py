from sentence_transformers import CrossEncoder

from labellens.retrieval.models import SearchHit

DEFAULT_RERANKER_MODEL = "BAAI/bge-reranker-base"


class CrossEncoderReranker:
    def __init__(self, model_name: str = DEFAULT_RERANKER_MODEL) -> None:
        self.model_name = model_name
        self.model = CrossEncoder(model_name)

    def rerank(self, query: str, hits: list[SearchHit], top_k: int = 10) -> list[SearchHit]:
        if not hits:
            return []

        # Build document text representation for candidate scoring
        pairs: list[tuple[str, str]] = [
            (
                query,
                f"{h.brand or ''} {h.name}. {h.payload.get('search_text', '')}".strip(),
            )
            for h in hits
        ]

        # Compute cross-attention logits
        scores = self.model.predict(pairs)

        scored_hits = list(zip(hits, scores, strict=False))
        scored_hits.sort(key=lambda x: x[1], reverse=True)

        reranked_hits: list[SearchHit] = []
        for rank, (hit, score) in enumerate(scored_hits[:top_k], start=1):
            reranked_hits.append(
                SearchHit(
                    id=hit.id,
                    code=hit.code,
                    name=hit.name,
                    brand=hit.brand,
                    score=float(score),
                    rank=rank,
                    match_source="reranked",
                    payload=hit.payload,
                )
            )
        return reranked_hits
