from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from app.api.dependencies import (
    get_adzuna_adapter,
    get_current_user,
    get_job_service,
    get_remoteok_adapter,
)
from app.api.schemas import (
    JobDetail,
    JobMatchResult,
    JobRefreshRequest,
    JobRefreshResponse,
    JobSearchResponse,
    JobSkills,
    JobWithSkills,
)
from app.domain.model.job import Job
from app.domain.ports.job_source_port import JobSourcePort
from app.domain.services.job_service import JobService
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)
router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.post("/search", response_model=JobSearchResponse)
async def search_jobs(
    top_k: int = 50,
    user_id: str = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service),
) -> JobSearchResponse:
    logger.info("job_search_request", user_id=user_id, top_k=top_k)

    try:
        job_matches, resume_id = job_service.search_jobs(user_id, top_k)

        matches = [
            JobMatchResult(
                job=_to_job_detail(match.job),
                similarity_score=match.similarity_score,
                skill_match_score=match.skill_match_score,
                combined_score=match.combined_score,
            )
            for match in job_matches
        ]

        return JobSearchResponse(matches=matches, total=len(matches), resume_id=resume_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{job_id}", response_model=JobWithSkills)
async def get_job(
    job_id: str,
    job_service: JobService = Depends(get_job_service),
) -> JobWithSkills:
    try:
        job = job_service.get_job_by_id(job_id)

        return JobWithSkills(
            **_to_job_detail(job).model_dump(),
            skills=_extract_skills(job) if job.has_extracted_skills() else None,
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/refresh", response_model=JobRefreshResponse)
async def refresh_jobs(
    request: JobRefreshRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_current_user),
    job_service: JobService = Depends(get_job_service),
    adzuna: JobSourcePort = Depends(get_adzuna_adapter),
    remoteok: JobSourcePort = Depends(get_remoteok_adapter),
) -> JobRefreshResponse:
    logger.info("job_refresh_request", user_id=user_id, query=request.query)

    sources = [adzuna, remoteok]

    background_tasks.add_task(
        job_service.refresh_jobs,
        job_sources=sources,
        query=request.query,
        location=request.location,
        limit=request.limit,
    )

    return JobRefreshResponse(
        jobs_fetched=0,
        jobs_saved=0,
        duplicates_skipped=0,
        sources=[source.get_source_name() for source in sources],
        message=f"Job refresh started for {len(sources)} sources",
    )


def _to_job_detail(job: Job) -> JobDetail:
    return JobDetail(
        id=job.id,
        title=job.title,
        company=job.company,
        description=job.description,
        url=job.url,
        location=job.location,
        salary=job.salary,
        source=job.source,
        posted_at=job.posted_at,
        fetched_at=job.fetched_at,
    )


def _extract_skills(job: Job) -> JobSkills:
    from app.api.schemas import JobSkills

    return JobSkills(
        required=job.required_skills or [],
        nice_to_have=job.nice_to_have_skills or [],
        tech_stack=job.tech_stack or [],
        seniority_level=job.seniority_level,
    )
