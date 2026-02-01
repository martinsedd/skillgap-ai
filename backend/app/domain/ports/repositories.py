from abc import ABC, abstractmethod

from app.domain.model.job import Job
from app.domain.model.resume import Resume


class ResumeRepository(ABC):
    """Port for resume persistence."""

    @abstractmethod
    def save(self, resume: Resume) -> Resume:
        ...

    @abstractmethod
    def find_by_id(self, resume_id: str) -> Resume | None:
        ...

    @abstractmethod
    def find_by_user_id(self, user_id: str) -> Resume | None:
        ...

    @abstractmethod
    def delete(self, resume_id: str) -> bool:
        ...


class JobRepository(ABC):
    """Port for job persistence."""

    @abstractmethod
    def save(self, job: Job) -> Job:
        ...

    @abstractmethod
    def bulk_save(self, jobs: list[Job]) -> list[Job]:
        ...

    @abstractmethod
    def find_by_id(self, job_id: str) -> Job | None:
        ...

    @abstractmethod
    def find_all(self, limit: int = 100, offset: int = 0) -> list[Job]:
        ...

    @abstractmethod
    def exists_by_dedup_hash(self, dedup_hash: str) -> bool:
        ...
