from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class SkillExtractionResult:
    """Result from extracting skills from resume text."""

    technical_skills: list[str]
    soft_skills: list[str]
    tools: list[str]
    frameworks: list[str]
    languages: list[str]


@dataclass
class JobSkillsResult:
    required_skills: list[str]
    nice_to_have_skills: list[str]
    tech_stack: list[str]
    seniority_level: str | None


@dataclass
class SkillGap:
    skill: str
    category: str
    importance: str
    recommendation: str


@dataclass
class GapAnalysisResult:
    matching_skills: list[str]
    missing_skills: list[SkillGap]
    overall_match_score: float
    summary: str
    recommendations: list[str]


class LLMPort(ABC):
    """Port for LLM interactions (skill extraction, gap analysis, interview questions)."""

    @abstractmethod
    def extract_skills_from_resume(self, resume_text: str) -> SkillExtractionResult:
        """
        Extract skills from resume text.

        Args:
            resume_text: Full text of the resume

        Returns:
            SkillExtractionResult with categorized skills

        Raises:
            LLMError: If extraction fails
        """
        ...

    @abstractmethod
    def extract_skills_from_job(self, job_description: str) -> JobSkillsResult:
        """
        Extract required skills and requirements from job description.

        Args:
            job_description: Job description text

        Returns:
            JobSkillsResult with required/nice-to-have skills

        Raises:
            LLMError: If extraction fails
        """
        ...

    @abstractmethod
    def analyze_gap(
        self,
        resume_text: str,
        job_description: str,
        resume_skills: list[str],
        job_required_skills: list[str],
    ) -> GapAnalysisResult:
        """
        Analyze skill gaps between resume and job requirements.

        Args:
            resume_text: Full resume for context
            job_description: Job description text for context
            resume_skills: Extracted skills from resume
            job-required_skills: Required skills from job

        Returns:
            GapAnalysisResult with matching/missing skills and recommendations

        Raises:
            LLMError: If analysis fails
        """
        ...

    @abstractmethod
    def generate_interview_question(
        self,
        job_description: str,
        topic: str,
        difficulty: str,
        previous_question: list[str],
    ) -> str:
        """
        Generate an interview question based on job requirements
        (Phase 3 - stub for now)

        Args:
            job_description: Job description for context
            topic: Skill or topic area to focus on
            difficulty: "easy", "medium", "hard"
            previous_questions: Questions already asked (to avoid duplicates)

        Returns:
            Interview question text

        Raises:
            LLMError: If genration fails
        """
        ...


class LLMError(Exception):
    ...


class LLMTimeoutError(LLMError):
    ...


class LLMParseError(LLMError):
    ...


class LLMServiceUnavailableError(LLMError):
    ...
