import logging
import uuid
from typing import Optional

from src.repositories.cv_repository import CVRepository
from src.services.ai_provider_service import AIProviderService

logger = logging.getLogger(__name__)


class CVEmbeddingService:
    def __init__(
        self,
        ai_service: AIProviderService | None = None,
    ) -> None:
        self._ai = ai_service or AIProviderService()

    async def generate_and_store(
        self,
        repo: CVRepository,
        cv_id: uuid.UUID,
        text: str,
    ) -> Optional[list[float]]:
        try:
            embedding = await self._ai.generate_embedding(text)
            if embedding is not None:
                await repo.update_embedding(cv_id, embedding)
                logger.info("Embedding stored cv_id=%s dim=%d", cv_id, len(embedding))
                return embedding
            else:
                logger.warning("Embedding generation returned None cv_id=%s", cv_id)
                return None
        except Exception:
            logger.exception("Embedding generation failed cv_id=%s", cv_id)
            return None
