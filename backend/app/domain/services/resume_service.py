import uuid
from io import BytesIO

from PyPDF2 import PdfReader

from app.domain.model.resume import Resume
from app.domain.ports.embedding_port import EmbeddingPort
from app.domain.ports.repositories import ResumeRepository
from app.domain.ports.vector_db_port import VectorDBPort
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)


class ResumeService:
    """Domain service for resume processing."""

    def __init__(
        self,
        resume_repository: ResumeRepository,
        embedding_service: EmbeddingPort,
        vector_db: VectorDBPort,
        storage_bucket: str,
    ) -> None:
        self.resume_repository = resume_repository
        self.embedding_service = embedding_service
        self.vector_db = vector_db
        self.storage_bucket = storage_bucket

    def process_resume_upload(self, user_id: str, pdf_bytes: bytes) -> Resume:
        """Process resume upload: extract text, save to DB."""
        logger.info("processing_resume_upload", user_id=user_id)

        text = self._extract_text_from_pdf(pdf_bytes)
        self._validate_text(text)

        resume = self._create_resume(user_id, text)
        saved_resume = self.resume_repository.save(resume)

        logger.info("resume_saved", resume_id=saved_resume.id)
        return saved_resume

    def generate_and_store_embedding(self, resume: Resume) -> None:
        """Generate embedding and store in vector DB."""
        logger.info("generating_embedding", resume_id=resume.id)

        embedding = self._generate_embedding(resume.text)
        self._store_in_vector_db(resume, embedding)

        logger.info("embedding_stored", resume_id=resume.id)

    def get_user_resume(self, user_id: str) -> Resume:
        resume = self.resume_repository.find_by_user_id(user_id)

        if not resume:
            raise ValueError(f"No resume found for user {user_id}")

        return resume

    def _extract_text_from_pdf(self, pdf_bytes) -> str:
        try:
            reader = PdfReader(BytesIO(pdf_bytes))
            text_parts = [page.extract_text() for page in reader.pages if page.extract_text()]
            return "\n".join(text_parts)
        except Exception as e:
            logger.error("pdf_extraction_failed", error=str(e))
            raise ValueError("Failed to extract text from PDF")

    def _validate_text(self, text: str) -> None:
        if not text or len(text.strip()) < 50:
            raise ValueError("Resume text too short or empty")

    def _create_resume(self, user_id: str, text: str) -> Resume:
        resume_id = str(uuid.uuid4())
        pinecone_id = f"resume-{user_id}"
        file_path = f"s3://{self.storage_bucket}/resumes/{user_id}/{resume_id}.pdf"

        return Resume(
            id=resume_id,
            user_id=user_id,
            text=text,
            file_path=file_path,
            pinecone_id=pinecone_id,
        )

    def _generate_embedding(self, text: str) -> list[float]:
        return self.embedding_service.generate_embedding(text)

    def _store_in_vector_db(self, resume: Resume, embedding: list[float]) -> None:
        self.vector_db.upsert_embedding(
            vector_id=resume.pinecone_id,
            embedding=embedding,
            metadata={
                "type": "resume",
                "user_id": resume.user_id,
                "resume_id": resume.id,
            },
        )
