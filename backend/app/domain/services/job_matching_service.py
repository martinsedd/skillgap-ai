from typing import Any

from app.domain.model.job import Job, JobMatch
from app.domain.model.resume import Resume
from app.domain.ports.embedding_port import EmbeddingPort
from app.domain.ports.vector_db_port import VectorDBPort
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)


class JobMatchingService:
    """Domain service for matching resumes to jobs."""

    def __init__(self, vector_db: VectorDBPort, embedding_service: EmbeddingPort):
        self.vector_db = vector_db
        self.embedding_service = embedding_service

    def find_similar_jobs(self, resume: Resume, top_k: int = 50) -> list[dict[str, Any]]:
        logger.info("finding_similar_jobs", resume_id=resume.id, top_k=top_k)

        resume_embedding = self._embed_resume(resume)
        results = self._search_vector_db(resume_embedding, top_k)

        logger.info("similar_jobs_found", resume_id=resume.id, count=len(results))
        return results

    def rank_jobs(self, resume: Resume, jobs: list[Job]) -> list[JobMatch]:
        """
        Rank provided jobs by relevance to resume.
        Combines vector similarity with skill matching.
        """
        logger.info("ranking_jobs", resume_id=resume.id, num_jobs=len(jobs))

        job_map = self._create_job_map(jobs)
        resume_embedding = self._embed_resume(resume)
        search_results = self._search_vector_db(resume_embedding, top_k=len(jobs))

        job_matches = self._build_job_matches(resume, job_map, search_results)
        sorted_matches = self._sort_by_combined_score(job_matches)

        logger.info("ranking_complete", resume_id=resume.id, matches_found=len(sorted_matches))
        return sorted_matches

    def _embed_resume(self, resume: Resume) -> list[float]:
        return self.embedding_service.generate_embedding(resume.text)

    def _search_vector_db(self, embedding: list[float], top_k: int) -> list[dict[str, Any]]:
        return self.vector_db.search_similar(
            query_embedding=embedding, filter_metadata={"type": "job"}, top_k=top_k
        )

    def _create_job_map(self, jobs: list[Job]) -> dict[str, Job]:
        return {job.id: job for job in jobs}

    def _build_job_matches(
        self,
        resume: Resume,
        job_map: dict[str, Job],
        search_results: list[dict[str, Any]],
    ) -> list[JobMatch]:
        job_matches: list[JobMatch] = []

        for result in search_results:
            job_match = self._create_job_match(resume, job_map, result)
            if job_match:
                job_matches.append(job_match)

        return job_matches

    def _create_job_match(
        self,
        resume: Resume,
        job_map: dict[str, Job],
        result: dict[str, Any],
    ) -> JobMatch | None:
        job_id = result["metadata"].get("job_id")
        job = job_map.get(job_id)

        if not job:
            logger.warning("job_not_found_in_map", job_id=job_id)
            return None

        return JobMatch(
            job=job,
            similarity_score=result["score"],
            skill_match_score=resume.matches_job(job),
        )

    def _sort_by_combined_score(self, matches: list[JobMatch]) -> list[JobMatch]:
        return sorted(matches, key=lambda x: x.combined_score, reverse=True)
