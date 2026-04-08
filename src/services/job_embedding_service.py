import logging
from typing import Optional

from src.services.ai_provider_service import AIProviderService

logger = logging.getLogger(__name__)


class JobEmbeddingService:
    def __init__(self, ai_service: AIProviderService | None = None) -> None:
        self._ai = ai_service or AIProviderService()

    async def generate_embedding(self, text: str) -> Optional[list[float]]:
        try:
            embedding = await self._ai.generate_embedding(text)
            return embedding
        except Exception:
            logger.exception("Embedding generation failed")
            return None
