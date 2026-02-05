from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.adapters.auth.stub_auth_adapter import create_stub_auth_adapter
from app.adapters.embedding.sentence_transformer_adapter import create_embedding_adapter
from app.adapters.job_sources.adzuna_adapter import create_adzuna_adapter
from app.adapters.job_sources.remoteok_adapter import create_remoteok_adapter
from app.adapters.llm.local_llm_adapter import create_local_llm_adapter
from app.adapters.repositories.job_repository import SQLAlchemyJobRepository
from app.adapters.repositories.resume_repository import SQLAlchemyResumeRepository
from app.adapters.vector_db.pinecone_adapter import create_pinecone_adapter
from app.core.config import settings
from app.domain.ports.auth_port import AuthPort
from app.domain.ports.embedding_port import EmbeddingPort
from app.domain.ports.job_source_port import JobSourcePort
from app.domain.ports.llm_port import LLMPort
from app.domain.ports.repositories import JobRepository, ResumeRepository
from app.domain.ports.vector_db_port import VectorDBPort
from app.domain.services.interview_service import InterviewService
from app.domain.services.job_matching_service import JobMatchingService
from app.domain.services.job_service import JobService
from app.domain.services.resume_service import ResumeService
from app.domain.services.skill_extraction_service import SkillExtractionService
from app.infrastructure.database.session import get_db
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)

# Singleton instances for expensive resources
_embedding_service: EmbeddingPort | None = None
_vector_db: VectorDBPort | None = None
_llm_service: LLMPort | None = None


def get_auth_service() -> AuthPort:
    return create_stub_auth_adapter()


def get_current_user(
    authorization: str = Header(...), auth_service: AuthPort = Depends(get_auth_service)
) -> str:
    """
    Extract and validate user from authorization header.
    Expected format: Bearer <token>
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header format")

    token = authorization.replace("Bearer ", "")
    user_id = auth_service.validate_token(token)

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    return user_id


def get_resume_repository(db: Session = Depends(get_db)) -> ResumeRepository:
    return SQLAlchemyResumeRepository(session=db)


def get_job_repository(db: Session = Depends(get_db)) -> JobRepository:
    return SQLAlchemyJobRepository(session=db)


def get_embedding_service() -> EmbeddingPort:
    global _embedding_service

    if _embedding_service is None:
        logger.info("initializing_embedding_service_singleton")
        _embedding_service = create_embedding_adapter(settings.EMBEDDING_MODEL)

    return _embedding_service


def get_vector_db() -> VectorDBPort:
    global _vector_db

    if _vector_db is None:
        logger.info("initializing_vector_db_singleton")
        embedding_service = get_embedding_service()
        _vector_db = create_pinecone_adapter(
            api_key=settings.PINECONE_API_KEY,
            index_name=settings.PINECONE_INDEX_NAME,
            environment=settings.PINECONE_ENVIRONMENT,
            dimension=embedding_service.get_embedding_dimension(),
        )

    return _vector_db


def get_adzuna_adapter() -> JobSourcePort:
    return create_adzuna_adapter(
        app_id=settings.ADZUNA_APP_ID,
        api_key=settings.ADZUNA_API_KEY,
        country=settings.ADZUNA_COUNTRY,
    )


def get_remoteok_adapter() -> JobSourcePort:
    return create_remoteok_adapter()


def get_job_matching_service(
    vector_db: VectorDBPort = Depends(get_vector_db),
    embedding_service: EmbeddingPort = Depends(get_embedding_service),
) -> JobMatchingService:
    return JobMatchingService(vector_db=vector_db, embedding_service=embedding_service)


def get_resume_service(
    resume_repo: ResumeRepository = Depends(get_resume_repository),
    embedding_service: EmbeddingPort = Depends(get_embedding_service),
    vector_db: VectorDBPort = Depends(get_vector_db),
) -> ResumeService:
    return ResumeService(
        resume_repository=resume_repo,
        embedding_service=embedding_service,
        vector_db=vector_db,
        storage_bucket=settings.STORAGE_BUCKET,
    )


def get_llm_service() -> LLMPort:
    global _llm_service

    if _llm_service is None:
        logger.info("initializing_llm_service_singleton")
        _llm_service = create_local_llm_adapter(
            endpoint=settings.LLM_ENDPOINT,
            timeout=50,
        )

    return _llm_service


def get_skill_extraction_service(
    llm_service: LLMPort = Depends(get_llm_service),
) -> SkillExtractionService:
    return SkillExtractionService(llm_service=llm_service)


def get_job_service(
    job_repo: JobRepository = Depends(get_job_repository),
    resume_repo: ResumeRepository = Depends(get_resume_repository),
    job_matching_service: JobMatchingService = Depends(get_job_matching_service),
    embedding_service: EmbeddingPort = Depends(get_embedding_service),
    vector_db: VectorDBPort = Depends(get_vector_db),
    skill_extraction_service: SkillExtractionService = Depends(get_skill_extraction_service),
) -> JobService:
    return JobService(
        job_repository=job_repo,
        resume_repository=resume_repo,
        job_matching_service=job_matching_service,
        embedding_service=embedding_service,
        vector_db=vector_db,
        skill_extraction_service=skill_extraction_service,
    )


def get_interview_service(
    llm_service: LLMPort = Depends(get_llm_service),
    skill_extraction_service: SkillExtractionService = Depends(get_skill_extraction_service),
    job_repo: JobRepository = Depends(get_job_repository),
    resume_repo: ResumeRepository = Depends(get_resume_repository),
) -> InterviewService:
    return InterviewService(
        llm_service=llm_service,
        skill_extraction_service=skill_extraction_service,
        job_repository=job_repo,
        resume_repository=resume_repo,
        total_questions=5,
    )
