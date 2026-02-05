from abc import ABC, abstractmethod
from typing import Any


class JobSourcePort(ABC):
    """Port for fetching jobs from external APIs."""

    @abstractmethod
    def fetch_jobs(
        self,
        query: str = "software engineer",
        location: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """
        Fetch jobs from external source.

        Returns list of raw job data:
        [
            {
                "external_id": "abc123",
                "title": "Senior Engineer",
                "company": "TechCorp",
                "description": "...",
                "url": "https://...",
                "location": "Remote",
                "salary": "$120k-$150k",
                "posted_at": "2025-01-31T12:00:00Z"
            },
            ...
        ]
        """
        ...

    @abstractmethod
    def get_source_name(self) -> str:
        ...
