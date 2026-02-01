from dataclasses import dataclass

from app.domain.models.job import Job


@dataclass
class Resume:
    """Domain model for resume."""

    id: str
    user_id: str
    text: str
    file_path: str
    pinecone_id: str

    def extract_skils(self) -> list[str]:
        """
        Extract skills from resume text.
        """

        # HACK: Placeholder - will enhance in Phase 2 with LLM
        keywords = [
            "python",
            "javascript",
            "typescript",
            "react",
            "node",
            "sql",
            "postgresql",
            "docker",
            "kubernetes",
            "aws",
            "gcp",
            "azure",
            "fastapi",
            "django",
            "flask",
            "vue",
            "angular",
            "java",
            "go",
            "rust",
            "c++",
            "machine learning",
            "deep learning",
            "llm",
        ]

        text_lower = self.text.lower()
        found_skills = [skill for skill in keywords if skill in text_lower]
        return list(set(found_skills))

    def matches_job(self, job: Job) -> float:
        """
        Calculates basic match score between resume and job.
        Returns score between 0.0 and 1.0.
        """
        # HACK: Simple implementation - will enhance to use vector similarity
        resume_skills = set(self.extract_skils())
        job_skills = set(job.required_skills or [])

        if not job_skills:
            return 0.0

        matching_skills = resume_skills.intersection(job_skills)
        return len(matching_skills) / len(job_skills)
