from sentence_transformers import SentenceTransformer

from app.domain.ports.embedding_port import EmbeddingPort
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)


class SentenceTransformerAdapter(EmbeddingPort):
    def __init__(self, model_name: str):
        self.model_name = model_name
        logger.info("loading_embedding_model", model=model_name)
        self.model = SentenceTransformer(model_name)
        dim = self.model.get_sentence_embedding_dimension()
        if dim is None:
            raise ValueError(f"Could not determine embedding dimension for model {model_name}")
        self.dimension: int = dim
        logger.info("embedding_model_loaded", model=model_name, dimension=self.dimension)

    def generate_embedding(self, text: str) -> list[float]:
        if not text or text.strip() == "":
            logger.warning("empty_text_for_embedding")
            return [0.0] * self.dimension

        logger.debug("generate_embedding", text_length=len(text))
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    def generate_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            logger.warning("empty_batch_for_embedding")
            return []

        logger.info("generating_batch_embeddins", batch_size=len(texts))
        embeddings = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=True)
        return embeddings.tolist()

    def get_embedding_dimension(self) -> int:
        return self.dimension


def create_embedding_adapter(model_name: str) -> SentenceTransformerAdapter:
    return SentenceTransformerAdapter(model_name=model_name)
