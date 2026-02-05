from abc import ABC, abstractmethod


class EmbeddingPort(ABC):
    """Port for generating text embeddings."""

    @abstractmethod
    def generate_embedding(self, text: str) -> list[float]:
        """
        Generate embedding vetor from text.
        Returns list of floats (768 dimensions for all-mpnet-base-v2).
        """
        ...

    @abstractmethod
    def generate_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        """
        Generate embeddings for multiple texts in batch.
        More efficient than calling generate_embedding multiple times.
        """
        ...

    @abstractmethod
    def get_embedding_dimension(self) -> int:
        """Return the dimension size of embeddings (e.g., 768)"""
        ...
