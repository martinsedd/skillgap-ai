import re
from datetime import datetime
from html import unescape
from typing import Any

import httpx

from app.domain.ports.job_source_port import JobSourcePort
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)


class RemoteOKAdapter(JobSourcePort):
    BASE_URL: str = "https://remoteok.com/api"

    def __init__(self):
        logger.info("remoteok_adapter_initialized")

    def fetch_jobs(
        self,
        query: str = "software engineer",
        location: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        logger.info("fetching_remoteok_jobs", query=query, limit=limit)

        try:
            response = self._make_request()
            jobs = self._parse_and_filter_response(response, query, limit)
            logger.info("remoteok_jobs_fetched", count=len(jobs))
            return jobs
        except Exception as e:
            logger.error("remoteok_fetch_failed", error=str(e), exc_info=True)
            return []

    def get_source_name(self) -> str:
        return "remoteok"

    def _make_request(self) -> list[dict[str, Any]]:
        headers = {"User-Agent": "SkillGap/1.0 (job aggregator)"}

        with httpx.Client(timeout=30.0) as client:
            response = client.get(self.BASE_URL, headers=headers)
            response.raise_for_status()
            data = response.json()

            if isinstance(data, list) and len(data) > 1:
                return data[1:]

        return []

    def _parse_and_filter_response(
        self, jobs_data: list[dict[str, Any]], query: str, limit: int
    ) -> list[dict[str, Any]]:
        jobs = []
        query_lower = query.lower()

        for item in jobs_data:
            if self._matches_query(item, query_lower):
                job = self._normalize_job(item)
                jobs.append(job)

                if len(jobs) >= limit:
                    break
        return jobs

    def _matches_query(self, item: dict[str, Any], query: str) -> bool:
        title = item.get("position", "").lower()
        tags = " ".join(item.get("tags", [])).lower()
        description = item.get("description", "").lower()

        search_text = f"{title} {tags} {description}"

        query_words = query.split()
        return any(word in search_text for word in query_words)

    def _normalize_job(self, item: dict[str, Any]) -> dict[str, Any]:
        description = item.get("description", "")
        cleaned_description = self._clean_html(description) if description else ""

        return {
            "external_id": str(item.get("id", "")),
            "title": item.get("position", ""),
            "company": item.get("company", "Unknown"),
            "description": cleaned_description,
            "url": item.get("url", ""),
            "location": "Remote",  # RemoteOK is remote-only
            "salary": self._format_salary(item),
            "posted_at": self._parse_epoch(item.get("epoch")),
        }

    def _format_salary(self, item: dict[str, Any]) -> str | None:
        """Format salary information."""
        salary_min = item.get("salary_min")
        salary_max = item.get("salary_max")

        if salary_min and salary_max:
            return f"${int(salary_min):,} - ${int(salary_max):,}"
        elif salary_min:
            return f"${int(salary_min):,}+"
        elif salary_max:
            return f"Up to ${int(salary_max):,}"

        return None

    def _clean_html(self, text: str) -> str:
        """Remove HTML tags and decode entities from text."""
        # Decode HTML entities
        text = unescape(text)

        # Remove HTML tags
        text = re.sub(r"<[^>]+>", "", text)

        # Fix common Unicode issues
        # Replace smart quotes and dashes
        text = text.replace("\u2018", "'").replace("\u2019", "'")  # Smart single quotes
        text = text.replace("\u201c", '"').replace("\u201d", '"')  # Smart double quotes
        text = text.replace("\u2013", "-").replace("\u2014", "-")  # En/em dashes
        text = text.replace("\u2026", "...")  # Ellipsis

        # Remove zero-width characters and other invisible Unicode
        text = re.sub(r"[\u200b-\u200d\ufeff]", "", text)

        # Normalize whitespace (including non-breaking spaces)
        text = re.sub(r"\s+", " ", text)

        # Remove any remaining problematic Unicode characters
        text = text.encode("ascii", "ignore").decode("ascii")

        return text.strip()

    def _parse_epoch(self, epoch: int | None) -> datetime | None:
        """Parse RemoteOK epoch timestamp to datetime."""
        if not epoch:
            return None

        try:
            return datetime.fromtimestamp(epoch)
        except (ValueError, TypeError, OSError):
            logger.warning("epoch_parse_failed", epoch=epoch)
            return None


def create_remoteok_adapter() -> RemoteOKAdapter:
    return RemoteOKAdapter()
