from typing import Sequence

import numpy as np
from sentence_transformers import SentenceTransformer

from labellens.config import settings
from labellens.embeddings.base import TextEmbedder

BGE_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


class BgeTextEmbedder(TextEmbedder):
    def __init__(self, model_name: str | None = None, use_query_prefix: bool = True)-> None:
        self.model_name = model_name or settings.text_embed_model
        self.use_query_prefix = use_query_prefix
        self.model = SentenceTransformer(self.model_name)
        self.dim = int(self.model.encode("test").shape[0])

    def embed_documents(self, texts: Sequence[str], batch_size: int = 64) -> np.ndarray:
        return self.model.encode(
            list(texts),
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=False,
            convert_to_numpy=True,
        )

    def embed_query(self, text: str) -> np.ndarray:
        if self.use_query_prefix:
            text = BGE_QUERY_PREFIX + text
        return self.model.encode(text, normalize_embeddings=True, convert_to_numpy=True)