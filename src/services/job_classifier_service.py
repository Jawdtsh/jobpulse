import logging

from src.services.ai_provider_service import AIProviderService
from src.services.exceptions import AIServiceUnavailableError

logger = logging.getLogger(__name__)


class JobClassifierService:
    def __init__(self, ai_service: AIProviderService | None = None) -> None:
        self._ai = ai_service or AIProviderService()

    async def classify_post(self, text: str) -> bool:
        prompt = f"Is this a job posting? Answer only yes or no:\n{text}"
        try:
            response = await self._ai.call_model(
                model_type="classifier",
                prompt=prompt,
                timeout=30,
            )
            return response.strip().lower().startswith("yes")
        except AIServiceUnavailableError:
            logger.error("All AI providers failed for classification")
            raise
