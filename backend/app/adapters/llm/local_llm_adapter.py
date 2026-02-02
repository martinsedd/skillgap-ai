import json

import httpx

from app.core.config import settings
from app.domain.ports.llm_port import (
    GapAnalysisResult,
    JobSkillsResult,
    LLMError,
    LLMParseError,
    LLMPort,
    LLMServiceUnavailableError,
    LLMTimeoutError,
    SkillExtractionResult,
    SkillGap,
)
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)


class LocalLLMAdapter(LLMPort):
    def __init__(self, endpoint: str, timeout: int = 60):
        self.endpoint = endpoint.rstrip("/")
        self.timeout = timeout
        logger.info("local_llm_adapter_initialized", endpoint=self.endpoint)

    def extract_skills_from_resume(self, resume_text: str) -> SkillExtractionResult:
        logger.info("extracting_skills_from_resume", text_length=len(resume_text))

        prompt = self._build_resume_skills_prompt(resume_text)

        try:
            response_text = self._generate(prompt)
            result = self._parse_resume_skills_response(response_text)
            logger.info(
                "resume_skills_extracted",
                technical_count=len(result.technical_skills),
                tools_count=len(result.tools),
            )
            return result
        except Exception as e:
            logger.error("resume_skill_extraction_failed", error=str(e), exc_info=True)
            raise

    def extract_skills_from_job(self, job_description: str) -> JobSkillsResult:
        logger.info("extracting_skills_from_job", text_length=len(job_description))

        prompt = self._build_job_skills_prompt(job_description)

        try:
            response_text = self._generate(prompt)
            result = self._parse_job_skills_response(response_text)
            logger.info(
                "job_skills_extracted",
                required_count=len(result.required_skills),
                nice_to_have_count=len(result.nice_to_have_skills),
            )
            return result
        except Exception as e:
            logger.error("job_skill_extraction_failed", error=str(e), exc_info=True)
            raise

    def analyze_gap(
        self,
        resume_text: str,
        job_description: str,
        resume_skills: list[str],
        job_required_skills: list[str],
    ) -> GapAnalysisResult:
        logger.info("analyzing_skill_gap")

        prompt = self._build_gap_analysis_prompt(
            job_description, resume_skills, job_required_skills
        )

        try:
            response_text = self._generate(prompt, max_tokens=1200)
            result = self._parse_gap_analysis_response(response_text)
            logger.info(
                "gap_analysis_complete",
                match_score=result.overall_match_score,
                missing_count=len(result.missing_skills),
            )
            return result
        except Exception as e:
            logger.error("gap_analysis_failed", error=str(e), exc_info=True)
            raise

    def generate_interview_question(
        self,
        job_description: str,
        topic: str,
        difficulty: str,
        previous_question: list[str],
    ) -> str:
        raise NotImplementedError("Interview questions coming in Phase 3")

    def _generate(self, prompt: str, temperature: float = 0.3, max_tokens: int = 800) -> str:
        """Make HTTP request to local LLM service."""
        url = f"{self.endpoint}/generate"

        payload = {
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(url, json=payload)
                response.raise_for_status()
                data = response.json()
                return data["text"]
        except httpx.TimeoutException as e:
            logger.error("llm_timeout", url=url, timeout=self.timeout)
            raise LLMTimeoutError(f"LLM service timed out after {self.timeout}s") from e
        except httpx.ConnectError as e:
            logger.error("llm_connection_failed", url=url)
            raise LLMServiceUnavailableError(f"Cannot connect to LLM service at {url}") from e
        except Exception as e:
            logger.error("llm_request_failed", error=str(e), exc_info=True)
            raise LLMError(f"LLM request failed: {str(e)}") from e

    def _build_resume_skills_prompt(self, resume_text: str) -> str:
        return f"""Extract skills from this resume and categorize them. Return ONLY
        valid JSON with no additional text.

        Resume:
        {resume_text[:2000]}

        Return JSON in this exact format:
        {{
            "technical_skills": ["skill1", "skill2"],
            "soft_skills": ["skill1", "skill2"],
            "tools": ["tool1", "tool2"],
            "frameworks": ["framework1", "framework2"],
            "languages": ["language1", "language2"]
        }}

        JSON:"""

    def _build_job_skills_prompt(self, job_description: str) -> str:
        return f"""Analyze this job description and extract requirements. Return ONLY
        valid JSON with no additional text.

        Job Description:
        {job_description[:2000]}

        Return JSON in this exact format:
        {{
            "required_skills": ["skill1", "skill2"],
            "nice_to_have_skills": ["skill1", "skill2"],
            "tech_stack": ["tech1", "tech2"],
            "seniority_level": "junior|mid|senior|staff"
        }}

        JSON:"""

    def _build_gap_analysis_prompt(
        self,
        job_description: str,
        resume_skills: list[str],
        job_required_skills: list[str],
    ) -> str:
        return f"""Analyze the skill gap between this resume and job requirements. Return
        ONLY valid JSON.

        Resume Skills: {', '.join(resume_skills[:30])}
        Job Required Skills: {', '.join(job_required_skills[:30])}

        Job Description:
        {job_description[:1500]}

        Return JSON in this exact format:
        {{
            "matching_skills": ["skill1", "skill2"]
            "missing_skills": [
                {{
                    "skill": "skill_name",
                    "category": "missing|weak|strong",
                    "importance": "critical|important|nice_to_have",
                    "recommendation": "learning tip"
                }}
            ],
            "overall_match_score": 0.75,
            "summary": "Brief summary of the gap analysis",
            "recommendation": ["recommendation1", "recommendation2"]
        }}

        JSON:"""

    def _parse_resume_skills_response(self, response: str) -> SkillExtractionResult:
        try:
            json_str = self._extract_json(response)
            data = json.loads(json_str)

            return SkillExtractionResult(
                technical_skills=data.get("technical_skills", []),
                soft_skills=data.get("soft_skills", []),
                tools=data.get("tools", []),
                frameworks=data.get("frameworks", []),
                languages=data.get("languages", []),
            )
        except json.JSONDecodeError as e:
            logger.error("json_parse_failed", response=response[:200])
            raise LLMParseError(f"Failed to parse resume skills JSON: {e}") from e

    def _parse_job_skills_response(self, response: str) -> JobSkillsResult:
        try:
            json_str = self._extract_json(response)
            data = json.loads(json_str)

            return JobSkillsResult(
                required_skills=data.get("required_skills", []),
                nice_to_have_skills=data.get("nice_to_have_skills", []),
                tech_stack=data.get("tech_stack", []),
                seniority_level=data.get("seniority_level"),
            )
        except json.JSONDecodeError as e:
            logger.error("json_parse_failed", response=response[:200])
            raise LLMParseError(f"Failed to parse job skills JSON: {e}") from e

    def _parse_gap_analysis_response(self, response: str) -> GapAnalysisResult:
        try:
            json_str = self._extract_json(response)
            data = json.loads(json_str)

            missing_skills = [
                SkillGap(
                    skill=gap["skill"],
                    category=gap["category"],
                    importance=gap["importance"],
                    recommendation=gap["recommendation"],
                )
                for gap in data.get("missing_skills", [])
            ]

            return GapAnalysisResult(
                matching_skills=data.get("matching_skills", []),
                missing_skills=missing_skills,
                overall_match_score=float(data.get("overall_match_score", 0.0)),
                summary=data.get("summary", ""),
                recommendations=data.get("recommendations", []),
            )
        except json.JSONDecodeError as e:
            logger.error("json_parse_failed", response=response[:200])
            raise LLMParseError(f"Failed to parse gap analysis JSON: {e}") from e

    def _extract_json(self, text: str) -> str:
        """Extract JSON object from text that might contain extra content."""
        start = text.find("{")
        end = text.find("}") + 1

        if start == -1 or end == 0:
            raise LLMParseError("No JSON object found in response")

        return text[start:end]


def create_local_llm_adapter(endpoint: str | None = None, timeout: int = 60) -> LocalLLMAdapter:
    llm_endpoint = endpoint or settings.LLM_ENDPOINT
    return LocalLLMAdapter(endpoint=llm_endpoint, timeout=timeout)
