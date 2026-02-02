import hashlib
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.domain.model.job import Job
from app.domain.ports.repositories import JobRepository
from app.infrastructure.database.models import JobModel, JobSource
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)


class SQLAlchemyJobRepository(JobRepository):
    """SQLAlchemy implementaion of JobRepository."""

    def __init__(self, session: Session):
        self.session = session

    def save(self, job: Job) -> Job:
        logger.info("saving_job", job_id=job.id, source=job.source)

        existing = self._find_model_by_id(job.id)

        if existing:
            self._update_model(existing, job)
        else:
            self._create_model(job)

        self.session.commit()
        logger.info("job_saved", job_id=job.id)
        return job

    def bulk_save(self, jobs: list[Job]) -> list[Job]:
        logger.info("bulk_saving_jobs", count=len(jobs))

        saved_jobs: list[Job] = []
        duplicates = 0

        for job in jobs:
            dedup_hash = self._compute_dedup_hash(job)

            if self.exists_by_dedup_hash(dedup_hash):
                logger.debug("duplicate_job_skipped", dedup_hash=dedup_hash, title=job.title)
                duplicates += 1
                continue

            model = self._create_model_with_hash(job, dedup_hash)
            self.session.add(model)
            saved_jobs.append(job)

        self.session.commit()
        logger.info("bulk_save_complete", saved=len(saved_jobs), duplicates=duplicates)
        return saved_jobs

    def find_by_id(self, job_id: str) -> Job | None:
        model = self._find_model_by_id(job_id)
        return self._to_domain(model) if model else None

    def find_all(self, limit: int = 100, offset: int = 0) -> list[Job]:
        models = (
            self.session.query(JobModel)
            .order_by(JobModel.fetched_at.desc())
            .limit(limit)
            .offset(offset)
            .all()
        )
        return [self._to_domain(model) for model in models]

    def exists_by_dedup_hash(self, dedup_hash: str) -> bool:
        return (
            self.session.query(JobModel).filter(JobModel.dedup_hash == dedup_hash).first()
        ) is not None

    def _find_model_by_id(self, job_id: str) -> JobModel:
        return self.session.query(JobModel).filter(JobModel.id == job_id).first()

    def _create_model(self, job: Job) -> JobModel:
        dedup_hash = self._compute_dedup_hash(job)
        return self._create_model_with_hash(job, dedup_hash)

    def _create_model_with_hash(self, job: Job, dedup_hash: str) -> JobModel:
        model = JobModel(
            id=job.id,
            external_id=job.external_id,
            source=JobSource(job.source),
            dedup_hash=dedup_hash,
            title=job.title,
            company=job.company,
            description=job.description,
            url=job.url,
            location=job.location,
            salary=job.salary,
            posted_at=job.posted_at,
            fetched_at=job.fetched_at or datetime.now(timezone.utc),
            pinecone_id=job.pinecone_id,
            extracted_skills=self._build_skills_json(job),
        )
        return model

    def _update_model(self, model: JobModel, job: Job) -> None:
        """Update existing JobModel from domain object."""
        setattr(model, "title", job.title)
        setattr(model, "company", job.company)
        setattr(model, "description", job.description)
        setattr(model, "url", job.url)
        setattr(model, "location", job.location)
        setattr(model, "salary", job.salary)
        setattr(model, "posted_at", job.posted_at)
        setattr(model, "fetched_at", job.fetched_at or datetime.now(timezone.utc))
        setattr(model, "extracted_skills", self._build_skills_json(job))

    def _compute_dedup_hash(self, job: Job) -> str:
        normalized = f"{job.title.lower()}|{job.company.lower()}|{(job.location or '').lower()}"
        return hashlib.sha256(normalized.encode()).hexdigest()

    def _build_skills_json(self, job: Job) -> dict | None:
        if not job.has_extracted_skills():
            return None

        return {
            "required": job.required_skills or [],
            "nice_to_have": job.nice_to_have_skills or [],
            "tech_stack": job.tech_stack or [],
            "seniority_level": job.seniority_level,
        }

    def _to_domain(self, model: JobModel) -> Job:
        skills = model.extracted_skills or {}

        return Job(
            id=str(model.id),
            external_id=str(model.external_id),
            source=str(model.source.value),
            title=str(model.title),
            company=str(model.company),
            description=str(model.description),
            url=str(model.url),
            pinecone_id=str(model.pinecone_id),
            location=str(model.location) if str(model.location) else None,
            salary=str(model.salary) if str(model.salary) else None,
            posted_at=(model.posted_at if isinstance(model.posted_at, datetime) else None),
            fetched_at=(model.fetched_at if isinstance(model.fetched_at, datetime) else None),
            required_skills=skills.get("required"),
            nice_to_have_skills=skills.get("nice_to_have"),
            tech_stack=skills.get("tech_stack"),
            seniority_level=skills.get("seniority_level"),
        )
