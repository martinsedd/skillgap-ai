from typing import Any, Dict, List, Optional

from pinecone import Pinecone, ServerlessSpec

from app.domain.ports.vector_db_port import VectorDBPort
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)


class PineconeAdapter(VectorDBPort):
    """Adapter for Pinecone vector database."""

    def __init__(self, api_key: str, index_name: str, environment: str, dimension: int):
        self.api_key = api_key
        self.index_name = index_name
        self.environment = environment
        self.dimension = dimension

        logger.info("initializing_pinecone", index_name=index_name)
        self.pc = Pinecone(api_key=api_key)
        self._ensure_index_exists()
        self.index = self.pc.Index(name=index_name)
        logger.info("pinecone_initialized", index_name=index_name)

    def upsert_embedding(
        self, vector_id: str, embedding: List[float], metadata: Dict[str, Any]
    ) -> None:
        """Insert or update a vector with metadata."""
        logger.debug("upserting_vector", vector_id=vector_id, metadata_keys=list(metadata.keys()))

        self.index.upsert(vectors=[(vector_id, embedding, metadata)])

    def search_similar(
        self,
        query_embedding: List[float],
        filter_metadata: Optional[Dict[str, Any]] = None,
        top_k: int = 50,
    ) -> List[Dict[str, Any]]:
        """Search for similar vectors."""
        logger.info(
            "searching_similar_vectors",
            top_k=top_k,
            has_filter=filter_metadata is not None,
        )

        results = self.index.query(
            vector=query_embedding,
            filter=filter_metadata,
            top_k=top_k,
            include_metadata=True,
        )

        matches = []
        results_dict = results.to_dict() if hasattr(results, "to_dict") else results  # type: ignore

        if isinstance(results_dict, dict) and "matches" in results_dict:
            for match in results_dict["matches"]:
                matches.append(
                    {
                        "id": match.get("id", ""),
                        "score": match.get("score", 0.0),
                        "metadata": match.get("metadata", {}),
                    }
                )

        logger.info("search_complete", matches_found=len(matches))
        return matches

    def delete_vector(self, vector_id: str) -> bool:
        """Delete a vector by ID."""
        logger.info("deleting_vector", vector_id=vector_id)

        try:
            self.index.delete(ids=[vector_id])
            return True
        except Exception as e:
            logger.error("delete_vector_failed", vector_id=vector_id, error=str(e))
            return False

    def delete_by_filter(self, filter_metadata: Dict[str, Any]) -> int:
        """Delete vectors matching filter."""
        logger.info("deleting_by_filter", filter=filter_metadata)

        try:
            self.index.delete(filter=filter_metadata)
            logger.info("delete_by_filter_complete")
            return 0  # Pinecone doesn't provide count
        except Exception as e:
            logger.error("delete_by_filter_failed", error=str(e))
            return 0

    def _ensure_index_exists(self) -> None:
        """Create index if it doesn't exist."""
        existing_indexes = [idx["name"] for idx in self.pc.list_indexes()]

        if self.index_name not in existing_indexes:
            logger.info("creating_pinecone_index", index_name=self.index_name)
            self.pc.create_index(
                name=self.index_name,
                dimension=self.dimension,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region=self.environment),
            )
            logger.info("pinecone_index_created", index_name=self.index_name)
        else:
            logger.info("pinecone_index_exists", index_name=self.index_name)


def create_pinecone_adapter(
    api_key: str, index_name: str, environment: str, dimension: int = 768
) -> PineconeAdapter:
    """Factory function to create Pinecone adapter."""
    return PineconeAdapter(
        api_key=api_key,
        index_name=index_name,
        environment=environment,
        dimension=dimension,
    )
