from abc import ABC, abstractmethod
from collections.abc import Sequence

import numpy as np


class TextEmbedder(ABC):
    dim: int

    @abstractmethod
    def embed_documents(self, texts: Sequence[str]) -> np.ndarray:
        """Return an array of shape (len(texts), dim), L2-normalized."""

    @abstractmethod
    def embed_query(self, text: str) -> np.ndarray:
        """Return a single vector of shape (dim,), L2-normalized."""
