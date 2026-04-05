import logging
from typing import Optional

from src.services.ai_provider_service import AIProviderService

logger = logging.getLogger(__name__)

_EXPECTED_DIMENSIONS = 768


class JobEmbeddingService:
    def __init__(self, ai_service: AIProviderService | None = None) -> None:
        self._ai = ai_service or AIProviderService()

    async def generate_embedding(self, text: str) -> Optional[list[float]]:
        try:
            embedding = await self._ai.generate_embedding(
                text, expected_dimensions=_EXPECTED_DIMENSIONS
            )
            if embedding is not None and len(embedding) != _EXPECTED_DIMENSIONS:
                logger.warning("Embedding dimension mismatch: got %d", len(embedding))
                return None
            return embedding
        except Exception as e:
            logger.error("Embedding generation failed: %s", e)
            return None
