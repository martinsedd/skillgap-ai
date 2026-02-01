from datetime import datetime
from typing import Any

import httpx

from app.domain.ports.job_source_port import JobSourcePort
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)


class AdzunaAdapter(JobSourcePort):
    BASE_URL = "https://api.adzuna.com/v1/api/jobs"

    def __init__(self, app_id: str, api_key: str, country: str = "us"):
        self.app_id = app_id
        self.api_key = api_key
        self.country = country
        logger.info("adzuna_adapter_initialized", country=country)

    def fetch_jobs(
        self,
        query: str = "software engineer",
        location: str | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        logger.info("fetching_adzuna_jobs", query=query, location=location, limit=limit)

        url = f"{self.BASE_URL}/{self.country}/search/1"
        params = self._build_params(query, location, limit)

        try:
            response = self._make_request(url, params)
            jobs = self._parse_response(response)
            logger.info("adzuna_jobs_fetched", count=len(jobs))
            return jobs
        except Exception as e:
            logger.error("adzuna_fetch_failed", error=str(e), exc_info=True)
            return []

    def get_source_name(self) -> str:
        return "adzuna"

    def _build_params(self, query: str, location: str | None, limit: int) -> dict[str, Any]:
        params: dict[str, Any] = {
            "app_id": self.app_id,
            "app_key": self.api_key,
            "results_per_page": min(limit, 50),
            "what": query,
            "content-type": "application/json",
        }

        if location:
            params["where"] = location

        return params

    def _make_request(self, url: str, params: dict[str, Any]) -> dict[str, Any]:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            return response.json()

    def _parse_response(self, response: dict[str, Any]) -> list[dict[str, Any]]:
        results = response.get("results", [])
        jobs = []

        for item in results:
            job = self._normalize_job(item)
            jobs.append(job)

        return jobs

    def _normalize_job(self, item: dict[str, Any]) -> dict[str, Any]:
        return {
            "external_id": item.get("id", ""),
            "title": item.get("title", ""),
            "company": item.get("company", {}).get("display_name", "Unknown"),
            "description": item.get("description", ""),
            "url": item.get("redirect_url", ""),
            "location": self._format_location(item.get("location", {})),
            "salary": self._format_salary(item),
            "posted_at": self._parse_date(item.get("created")),
        }

    def _format_location(self, location: dict[str, Any]) -> str:
        display_name = location.get("display_name", "")
        if display_name:
            return display_name

        area = location.get("area", [])
        return ", ".join(area) if area else "Remote"

    def _format_salary(self, item: dict[str, Any]) -> str | None:
        salary_min = item.get("salary_min")
        salary_max = item.get("salary_max")

        if salary_min and salary_max:
            return f"${int(salary_min):,} - ${int(salary_max):,}"
        elif salary_min:
            return f"${int(salary_min):,}+"
        elif salary_max:
            return f"Up to ${int(salary_max):,}"

        return None

    def _parse_date(self, date_str: str | None) -> datetime | None:
        if not date_str:
            return None

        try:
            # INFO: Adzuna uses ISO 8601 format
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            logger.warning("date_parse_failed", date_str=date_str)
            return None


def create_adzuna_adapter(app_id: str, api_key: str, country: str = "us") -> AdzunaAdapter:
    return AdzunaAdapter(app_id=app_id, api_key=api_key, country=country)
