from app.domain.model.job import Job
from app.domain.model.resume import Resume
from app.domain.ports.llm_port import (
    GapAnalysisResult,
    JobSkillsResult,
    LLMPort,
    SkillExtractionResult,
)
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)


class SkillExtractionService:
    def __init__(self, llm_service: LLMPort):
        self.llm_service = llm_service

    def extract_resume_skills(self, resume: Resume) -> SkillExtractionResult:
        logger.info("extracting_resume_skills", resume_id=resume.id)

        if not resume.text or len(resume.text.strip()) < 50:
            logger.warning("resume_text_too_short", resume_id=resume.id)
            return SkillExtractionResult(
                technical_skills=[],
                soft_skills=[],
                tools=[],
                frameworks=[],
                languages=[],
            )

        return self.llm_service.extract_skills_from_resume(resume.text)

    def extract_job_skills(self, job: Job) -> JobSkillsResult:
        logger.info("extracting_job_skills", job_id=job.id)

        if not job.description or len(job.description.strip()) < 50:
            logger.warning("job_description_too_short", job_id=job.id)
            return JobSkillsResult(
                required_skills=[],
                nice_to_have_skills=[],
                tech_stack=[],
                seniority_level=None,
            )

        return self.llm_service.extract_skills_from_job(job.description)

    def update_job_with_skills(self, job: Job) -> Job:
        logger.info("updating_job_with_skills", job_id=job.id)

        skills_result = self.extract_job_skills(job)

        # Update job model with extracted skills
        job.required_skills = skills_result.required_skills
        job.nice_to_have_skills = skills_result.nice_to_have_skills
        job.tech_stack = skills_result.tech_stack
        job.seniority_level = skills_result.seniority_level

        logger.info(
            "job_skills_updated",
            job_id=job.id,
            required_count=len(job.required_skills or []),
        )

        return job

    def analyze_gap(self, resume: Resume, job: Job) -> GapAnalysisResult:
        logger.info("analyzing_gap", resume_id=resume.id, job_id=job.id)

        resume_skills = resume.extract_skills()
        job_required_skills = job.required_skills or []

        if not job_required_skills:
            logger.warning("no_job_skills_to_compare", job_id=job.id)
            return GapAnalysisResult(
                matching_skills=[],
                missing_skills=[],
                overall_match_score=0.0,
                summary="Job has no extracted skills to compare agains.",
                recommendations=[],
            )

        return self.llm_service.analyze_gap(
            resume_text=resume.text,
            job_description=job.description,
            resume_skills=resume_skills,
            job_required_skills=job_required_skills,
        )

    def get_all_resume_skills(self, resume: Resume) -> list[str]:
        skills_result = self.extract_resume_skills(resume)

        all_skills = (
            skills_result.technical_skills
            + skills_result.tools
            + skills_result.frameworks
            + skills_result.languages
        )

        return list(set(all_skills))
