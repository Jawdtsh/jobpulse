from unittest.mock import AsyncMock, patch

import pytest

from src.services.job_embedding_service import JobEmbeddingService


@pytest.fixture
def mock_ai():
    with patch("src.services.job_embedding_service.AIProviderService") as mock_cls:
        instance = AsyncMock()
        mock_cls.return_value = instance
        yield instance


class TestVectorGeneration:
    @pytest.mark.asyncio
    async def test_returns_768_dim_vector(self, mock_ai):
        mock_ai.generate_embedding.return_value = [0.1] * 768
        svc = JobEmbeddingService()
        result = await svc.generate_embedding("job post text")
        assert result is not None
        assert len(result) == 768

    @pytest.mark.asyncio
    async def test_validates_dimensions(self, mock_ai):
        mock_ai.generate_embedding.return_value = [0.1] * 512
        svc = JobEmbeddingService()
        result = await svc.generate_embedding("text")
        assert result is None


class TestRetryOnDimensionMismatch:
    @pytest.mark.asyncio
    async def test_retries_on_wrong_size(self, mock_ai):
        mock_ai.generate_embedding.side_effect = [
            [0.1] * 512,
            [0.1] * 768,
        ]
        svc = JobEmbeddingService()
        result = await svc.generate_embedding("text")
        assert result is not None
        assert len(result) == 768


class TestNullOnAllFailure:
    @pytest.mark.asyncio
    async def test_returns_none_on_failure(self, mock_ai):
        mock_ai.generate_embedding.side_effect = Exception("fail")
        svc = JobEmbeddingService()
        result = await svc.generate_embedding("text")
        assert result is None
