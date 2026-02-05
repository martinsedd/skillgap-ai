import uuid
from datetime import datetime, timezone


from app.domain.model.job import Job, JobMatch
from app.domain.model.resume import Resume
from app.domain.ports.embedding_port import EmbeddingPort
from app.domain.ports.job_source_port import JobSourcePort
from app.domain.ports.repositories import JobRepository, ResumeRepository
from app.domain.ports.vector_db_port import VectorDBPort
from app.domain.services.job_matching_service import JobMatchingService
from app.domain.services.skill_extraction_service import SkillExtractionService
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)


class JobService:
    def __init__(
        self,
        job_repository: JobRepository,
        resume_repository: ResumeRepository,
        job_matching_service: JobMatchingService,
        embedding_service: EmbeddingPort,
        vector_db: VectorDBPort,
        skill_extraction_service: SkillExtractionService,
    ) -> None:
        self.job_repository = job_repository
        self.resume_repository = resume_repository
        self.job_matching_service = job_matching_service
        self.embedding_service = embedding_service
        self.vector_db = vector_db
        self.skill_extraction_service = skill_extraction_service

    def search_jobs(self, user_id: str, top_k: int = 50) -> tuple[list[JobMatch], str]:
        logger.info("searching_jobs", user_id=user_id, top_k=top_k)

        resume = self._get_user_resume(user_id)
        search_results = self.job_matching_service.find_similar_jobs(resume, top_k)
        job_ids = [result["metadata"]["job_id"] for result in search_results]

        jobs = self._fetch_jobs_by_ids(job_ids)
        job_matches = self.job_matching_service.rank_jobs(resume, jobs)

        logger.info("jobs_searched", user_id=user_id, matches_found=len(job_matches))
        return job_matches, resume.id

    def get_job_by_id(self, job_id: str) -> Job:
        job = self.job_repository.find_by_id(job_id)

        if not job:
            raise ValueError(f"Job {job_id} not found")

        return job

    def refresh_jobs(
        self,
        job_sources: list[JobSourcePort],
        query: str,
        location: str | None,
        limit: int,
    ) -> tuple[int, int, int]:
        logger.info("refreshing_jobs", query=query, location=location, limit=limit)

        all_jobs = self._fetch_from_sources(job_sources, query, location, limit)

        logger.info("extracting_skills_from_job", count=len(all_jobs))
        for job in all_jobs:
            try:
                self.skill_extraction_service.update_job_with_skills(job)
            except Exception as e:
                logger.warning("skill_extraction_failed", job_id=job.id, error=str(e))

        saved_jobs = self.job_repository.bulk_save(all_jobs)
        self._generate_embeddings_for_jobs(saved_jobs)

        fetched_count = len(all_jobs)
        saved_count = len(saved_jobs)
        duplicates = fetched_count - saved_count

        logger.info(
            "jobs_refreshed",
            fetched=fetched_count,
            saved=saved_count,
            duplicates=duplicates,
        )
        return fetched_count, saved_count, duplicates

    def get_gap_analysis(self, user_id: str, job_id: str):
        logger.info("getting_gap_analysis", user_id=user_id, job_id=job_id)

        resume = self._get_user_resume(user_id)
        job = self.get_job_by_id(job_id)

        return self.skill_extraction_service.analyze_gap(resume, job)

    def _get_user_resume(self, user_id: str) -> Resume:
        resume = self.resume_repository.find_by_user_id(user_id)

        if not resume:
            raise ValueError(f"No resume found for user {user_id}")

        return resume

    def _fetch_jobs_by_ids(self, job_ids: list[str]) -> list[Job]:
        jobs = []
        for job_id in job_ids:
            job = self.job_repository.find_by_id(job_id)
            if job:
                jobs.append(job)
        return jobs

    def _fetch_from_sources(
        self, sources: list[JobSourcePort], query: str, location: str | None, limit: int
    ) -> list[Job]:
        all_jobs = []

        for source in sources:
            raw_jobs = source.fetch_jobs(query, location, limit)
            jobs = self._convert_raw_jobs_to_domain(raw_jobs, source.get_source_name())
            all_jobs.extend(jobs)

        return all_jobs

    def _convert_raw_jobs_to_domain(self, raw_jobs: list[dict], source: str) -> list[Job]:
        jobs = []

        for raw_job in raw_jobs:
            job = Job(
                id=str(uuid.uuid4()),
                external_id=raw_job["external_id"],
                source=source,
                title=raw_job["title"],
                company=raw_job["company"],
                description=raw_job["description"],
                url=raw_job["url"],
                pinecone_id=f"job-{uuid.uuid4()}",
                location=raw_job.get("location"),
                salary=raw_job.get("salary"),
                posted_at=raw_job.get("posted_at"),
                fetched_at=datetime.now(timezone.utc),
            )
            jobs.append(job)

        return jobs

    def _generate_embeddings_for_jobs(self, jobs: list[Job]) -> None:
        if not jobs:
            return

        logger.info("generating_job_embeddings", count=len(jobs))

        descriptions = [job.description for job in jobs]
        embeddings = self.embedding_service.generate_embeddings_batch(descriptions)

        for job, embedding in zip(jobs, embeddings):
            self.vector_db.upsert_embedding(
                vector_id=job.pinecone_id,
                embedding=embedding,
                metadata={"type": "job", "job_id": job.id, "source": job.source},
            )

        logger.info("job_embeddings_generated", count=len(jobs))
