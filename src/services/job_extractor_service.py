import json
import logging
from typing import Optional

from pydantic import BaseModel

from src.services.ai_provider_service import AIProviderService
from src.services.exceptions import AIServiceUnavailableError

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """Extract job information from the following text.
Return a JSON object with these fields:
- title: Job title (string or null)
- company: Company name (string or null)
- location: Job location (string or null)
- salary_min: Minimum salary (integer or null)
- salary_max: Maximum salary (integer or null)
- salary_currency: Currency code, default "USD" (string)
- description: Job description (string or null)
- requirements: List of requirements (array of strings or null)
- skills: List of skills (array of strings or null)

Return ONLY valid JSON, no other text."""


class JobExtractionResult(BaseModel):
    title: Optional[str] = None
    company: Optional[str] = None
    location: Optional[str] = None
    salary_min: Optional[int] = None
    salary_max: Optional[int] = None
    salary_currency: str = "USD"
    description: Optional[str] = None
    requirements: Optional[list[str]] = None
    skills: Optional[list[str]] = None


class JobExtractorService:
    def __init__(self, ai_service: AIProviderService | None = None) -> None:
        self._ai = ai_service or AIProviderService()

    async def extract_job_data(self, text: str) -> JobExtractionResult:
        try:
            response = await self._ai.call_model(
                model_type="extractor",
                prompt=text,
                system_prompt=_SYSTEM_PROMPT,
                response_format={"type": "json_object"},
                timeout=30,
            )
            return self._parse_response(response)
        except AIServiceUnavailableError:
            logger.error("All AI providers failed for extraction")
            raise

    def _parse_response(self, response: str) -> JobExtractionResult:
        try:
            data = json.loads(response)
            return JobExtractionResult(**data)
        except (json.JSONDecodeError, Exception) as e:
            logger.warning("Failed to parse extraction response: %s", e)
            return JobExtractionResult()
