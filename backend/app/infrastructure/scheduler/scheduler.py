from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from app.adapters.embedding.sentence_transformer_adapter import create_embedding_adapter
from app.adapters.job_sources.adzuna_adapter import create_adzuna_adapter
from app.adapters.job_sources.remoteok_adapter import create_remoteok_adapter
from app.adapters.llm.local_llm_adapter import create_local_llm_adapter
from app.adapters.repositories.job_repository import SQLAlchemyJobRepository
from app.adapters.repositories.resume_repository import SQLAlchemyResumeRepository
from app.adapters.vector_db.pinecone_adapter import create_pinecone_adapter
from app.api.dependencies import get_job_service
from app.core.config import settings
from app.domain.services.job_matching_service import JobMatchingService
from app.domain.services.skill_extraction_service import SkillExtractionService
from app.infrastructure.database.session import get_db_context
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)
scheduler: AsyncIOScheduler | None = None


def create_scheduler() -> AsyncIOScheduler:
    logger.info("creating_scheduler")

    scheduler = AsyncIOScheduler()

    cron_parts = settings.JOB_REFRESH_CRON.split()

    if len(cron_parts) != 5:
        logger.error("invalid_cron_expression", cron=settings.JOB_REFRESH_CRON)
        raise ValueError(f"Invalid cron expression: {settings.JOB_REFRESH_CRON}")

    minute, hour, day, month, day_of_week = cron_parts

    scheduler.add_job(
        func=refresh_jobs_task,
        trigger=CronTrigger(
            minute=minute,
            hour=hour,
            day=day,
            month=month,
            day_of_week=day_of_week,
        ),
        id="job_refresh",
        name="Daily Job Refresh",
        replace_existing=True,
    )

    logger.info(
        "scheduler_configured",
        cron=settings.JOB_REFRESH_CRON,
        job_id="job_refresh",
    )

    return scheduler


def refresh_jobs_task():
    logger.info("job_refresh_task_started")

    try:
        with get_db_context() as db:
            job_repo = SQLAlchemyJobRepository(session=db)
            resume_repo = SQLAlchemyResumeRepository(session=db)

            embedding_service = create_embedding_adapter(settings.EMBEDDING_MODEL)

            vector_db = create_pinecone_adapter(
                api_key=settings.PINECONE_API_KEY,
                index_name=settings.PINECONE_INDEX_NAME,
                environment=settings.PINECONE_ENVIRONMENT,
                dimension=embedding_service.get_embedding_dimension(),
            )

            llm_service = create_local_llm_adapter(
                endpoint=settings.LLM_ENDPOINT,
                timeout=60,
            )

            skill_extraction_service = SkillExtractionService(llm_service=llm_service)

            job_matching_service = JobMatchingService(
                vector_db=vector_db, embedding_service=embedding_service
            )

            job_service = get_job_service(
                job_repo=job_repo,
                resume_repo=resume_repo,
                job_matching_service=job_matching_service,
                embedding_service=embedding_service,
                vector_db=vector_db,
                skill_extraction_service=skill_extraction_service,
            )

            adzuna = create_adzuna_adapter(
                app_id=settings.ADZUNA_APP_ID,
                api_key=settings.ADZUNA_API_KEY,
                country=settings.ADZUNA_COUNTRY,
            )

            remoteok = create_remoteok_adapter()

            sources = [adzuna, remoteok]

            fetched, saved, duplicates = job_service.refresh_jobs(
                job_sources=sources, query="software engineer", location=None, limit=50
            )

            logger.info(
                "job_refresh_task_completed",
                fetched=fetched,
                saved=saved,
                duplicates=duplicates,
            )
    except Exception as e:
        logger.error("job_refresh_task_failed", error=str(e), exc_info=True)


def start_scheduler():
    global scheduler

    if scheduler is None:
        scheduler = create_scheduler()

    scheduler.start()
    logger.info("scheduler started")


def shutdown_scheduler():
    global scheduler

    if scheduler is not None:
        scheduler.shutdown(wait=True)
        logger.info("scheduler_shutdown")
        scheduler = None
