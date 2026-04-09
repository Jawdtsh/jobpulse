import uuid
from unittest.mock import AsyncMock

import pytest

from src.services.cv_embedding import CVEmbeddingService


@pytest.fixture
def mock_ai_service():
    svc = AsyncMock()
    return svc


@pytest.fixture
def mock_repo():
    return AsyncMock()


@pytest.fixture
def service(mock_ai_service):
    return CVEmbeddingService(ai_service=mock_ai_service)


class TestCVEmbeddingGenerateAndStore:
    @pytest.mark.asyncio
    async def test_stores_embedding_on_success(
        self, service, mock_ai_service, mock_repo
    ):
        cv_id = uuid.uuid4()
        embedding = [0.1] * 768
        mock_ai_service.generate_embedding.return_value = embedding

        result = await service.generate_and_store(mock_repo, cv_id, "sample text")

        assert result == embedding
        mock_repo.update_embedding.assert_called_once_with(cv_id, embedding)

    @pytest.mark.asyncio
    async def test_returns_none_when_embedding_is_none(
        self, service, mock_ai_service, mock_repo
    ):
        cv_id = uuid.uuid4()
        mock_ai_service.generate_embedding.return_value = None

        result = await service.generate_and_store(mock_repo, cv_id, "text")

        assert result is None
        mock_repo.update_embedding.assert_not_called()

    @pytest.mark.asyncio
    async def test_returns_none_on_exception(self, service, mock_ai_service, mock_repo):
        cv_id = uuid.uuid4()
        mock_ai_service.generate_embedding.side_effect = RuntimeError("API error")

        result = await service.generate_and_store(mock_repo, cv_id, "text")

        assert result is None
        mock_repo.update_embedding.assert_not_called()

    @pytest.mark.asyncio
    async def test_passes_uuid_not_string_to_repo(
        self, service, mock_ai_service, mock_repo
    ):
        cv_id = uuid.uuid4()
        embedding = [0.2] * 768
        mock_ai_service.generate_embedding.return_value = embedding

        await service.generate_and_store(mock_repo, cv_id, "text")

        call_args = mock_repo.update_embedding.call_args
        assert isinstance(call_args[0][0], uuid.UUID)
        assert call_args[0][0] == cv_id
