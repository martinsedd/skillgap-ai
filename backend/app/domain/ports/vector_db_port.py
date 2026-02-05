from abc import ABC, abstractmethod
from typing import Any


class VectorDBPort(ABC):
    """Port for vector database operations."""

    @abstractmethod
    def upsert_embedding(
        self, vector_id: str, embedding: list[float], metadata: dict[str, Any]
    ) -> None:
        ...

    @abstractmethod
    def search_similar(
        self,
        query_embedding: list[float],
        filter_metadata: dict[str, Any] | None = None,
        top_k: int = 50,
    ) -> list[dict[str, Any]]:
        """
        Search for similar vectors.

        Returns list of matches with structure:
        [
            {
                "id": "vector_id",
                "score": 0.95,
                "metadata": { ... }
            },
            ...
        ]
        """
        ...

    @abstractmethod
    def delete_vector(self, vector_id: str) -> bool:
        ...

    @abstractmethod
    def delete_by_filter(self, filter_metadata: dict[str, Any]) -> int:
        ...
