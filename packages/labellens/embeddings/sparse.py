from typing import Sequence

from fastembed import SparseTextEmbedding
from qdrant_client import models
from fastembed.sparse import SparseEmbedding

from labellens.config import settings


class Bm25SparseEmbedder:
    """BM25-style sparse vectors: great for exact words, brands and E-numbers."""

    def __init__(self, model_name: str | None = None)-> None:
        self.model = SparseTextEmbedding(model_name or settings.sparse_embed_model)

    @staticmethod
    def _to_qdrant(emb:SparseEmbedding) -> models.SparseVector:
        return models.SparseVector(indices=emb.indices.tolist(), values=emb.values.tolist())

    def embed_documents(self, texts: Sequence[str]) -> list[models.SparseVector]:
        return [self._to_qdrant(e) for e in self.model.embed(list(texts))]

    def embed_query(self, text: str) -> models.SparseVector:
        return self._to_qdrant(next(iter(self.model.query_embed(text))))