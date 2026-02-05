from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass
class Job:
    """Domain model for job posting."""

    id: str
    external_id: str
    source: str
    title: str
    company: str
    description: str
    url: str
    pinecone_id: str
    location: str | None = None
    salary: str | None = None
    posted_at: datetime | None = None
    fetched_at: datetime | None = None
    required_skills: list[str] | None = None
    nice_to_have_skills: list[str] | None = None
    tech_stack: list[str] | None = None
    seniority_level: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "external_id": self.external_id,
            "source": self.source,
            "title": self.title,
            "company": self.company,
            "description": self.description,
            "url": self.url,
            "location": self.location,
            "salary": self.salary,
            "posted_at": self.posted_at.isoformat() if self.posted_at else None,
            "fetched_at": self.fetched_at.isoformat() if self.fetched_at else None,
            "required_skills": self.required_skills,
            "nice_to_have_skills": self.nice_to_have_skills,
            "tech_stack": self.tech_stack,
            "seniority_level": self.seniority_level,
        }

    def has_extracted_skills(self) -> bool:
        return self.required_skills is not None


@dataclass
class JobMatch:
    """Represents a job matched to a resume with similarity score."""

    job: Job
    similarity_score: float
    skill_match_score: float

    @property
    def combined_score(self) -> float:
        """Weighted combination of similarity and skill match."""
        return (0.7 * self.similarity_score) + (0.3 * self.skill_match_score)
