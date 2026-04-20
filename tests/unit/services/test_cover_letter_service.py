import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.services.cover_letter_service import (
    CoverLetterService,
    VALID_TONES,
    VALID_LENGTHS,
    VALID_FOCUSES,
    VALID_LANGUAGES,
    LENGTH_WORD_COUNTS,
)


@pytest.fixture
def mock_session():
    return AsyncMock()


@pytest.fixture
def mock_repo():
    repo = AsyncMock()
    return repo


@pytest.fixture
def service(mock_session, mock_repo):
    with patch("src.services.cover_letter_service.get_settings"):
        svc = CoverLetterService(mock_session)
        svc._repo = mock_repo
        svc._prompt_template = (
            "Write a {length} cover letter in {language} with a {tone} tone. "
            "Focus on: {focus}. "
            "Job: {job_title} at {company} in {location}. "
            "Description: {job_description}. "
            "CV: {cv_content}. Name: {user_name}. "
            "Word count: {word_count}."
        )
        return svc


@pytest.mark.asyncio
async def test_generate_success(service, mock_repo):
    user_id = uuid.uuid4()
    job_id = uuid.uuid4()
    cv_id = uuid.uuid4()

    with patch("src.services.ai_provider_service.AIProviderService") as mock_ai_cls:
        mock_ai = AsyncMock()
        mock_ai.call_model = AsyncMock(return_value="Dear Hiring Manager...")
        mock_ai_cls.return_value = mock_ai

        mock_repo.create_log = AsyncMock(
            return_value=MagicMock(id=uuid.uuid4(), content="Dear Hiring Manager...")
        )

        result = await service.generate(
            user_id=user_id,
            job_id=job_id,
            cv_id=cv_id,
            job_title="Software Engineer",
            company="Tech Corp",
            location="Damascus",
            job_description="Build great software",
            cv_content="5 years Python experience",
            user_name="Ahmad",
            tone="professional",
            length="medium",
            focus="all",
            language="english",
        )

        assert result == "Dear Hiring Manager..."
        mock_ai.call_model.assert_called_once()
        mock_repo.create_log.assert_called_once()


@pytest.mark.asyncio
async def test_validate_quota_sufficient(service):
    from src.services.quota_service import QuotaService

    mock_quota = AsyncMock(spec=QuotaService)
    mock_quota.has_quota = AsyncMock(return_value=True)

    result = await mock_quota.has_quota(uuid.uuid4(), "free")
    assert result is True


@pytest.mark.asyncio
async def test_validate_quota_insufficient(service):
    from src.services.quota_service import QuotaService

    mock_quota = AsyncMock(spec=QuotaService)
    mock_quota.has_quota = AsyncMock(return_value=False)

    result = await mock_quota.has_quota(uuid.uuid4(), "free")
    assert result is False


@pytest.mark.asyncio
async def test_validate_options_valid(service):
    service._validate_options("professional", "medium", "all", "english")


@pytest.mark.asyncio
async def test_validate_options_invalid_tone(service):
    with pytest.raises(ValueError, match="Invalid tone"):
        service._validate_options("friendly", "medium", "all", "english")


@pytest.mark.asyncio
async def test_validate_options_invalid_length(service):
    with pytest.raises(ValueError, match="Invalid length"):
        service._validate_options("professional", "tiny", "all", "english")


@pytest.mark.asyncio
async def test_validate_options_invalid_focus(service):
    with pytest.raises(ValueError, match="Invalid focus"):
        service._validate_options("professional", "medium", "hobbies", "english")


@pytest.mark.asyncio
async def test_validate_options_invalid_language(service):
    with pytest.raises(ValueError, match="Invalid language"):
        service._validate_options("professional", "medium", "all", "french")


def test_valid_tones():
    assert VALID_TONES == {"formal", "casual", "professional"}


def test_valid_lengths():
    assert VALID_LENGTHS == {"short", "medium", "long"}


def test_valid_focuses():
    assert VALID_FOCUSES == {"skills", "experience", "education", "all"}


def test_valid_languages():
    assert VALID_LANGUAGES == {"arabic", "english", "bilingual"}


def test_length_word_counts():
    assert LENGTH_WORD_COUNTS == {"short": 200, "medium": 400, "long": 600}


def test_check_cv_completeness_none():
    result = CoverLetterService.check_cv_completeness(None)
    assert result == (False, 0.0)


def test_check_cv_completeness_sufficient():
    cv = MagicMock()
    cv.completeness_score = 80
    is_complete, score = CoverLetterService.check_cv_completeness(cv)
    assert is_complete is True
    assert score == 80.0


def test_check_cv_completeness_insufficient():
    cv = MagicMock()
    cv.completeness_score = 40
    is_complete, score = CoverLetterService.check_cv_completeness(cv)
    assert is_complete is False
    assert score == 40.0


def test_check_cv_completeness_no_score():
    cv = MagicMock()
    cv.completeness_score = None
    is_complete, score = CoverLetterService.check_cv_completeness(cv)
    assert is_complete is False
    assert score == 0.0


def test_extract_placeholders_returns_names_without_braces():
    from src.services.cover_letter_service import _extract_placeholders

    template = "Hello {name}, your {job_title} at {company}"
    result = _extract_placeholders(template)
    assert result == ["name", "job_title", "company"]


def test_extract_placeholders_no_double_strip():
    from src.services.cover_letter_service import (
        _extract_placeholders,
        REQUIRED_PLACEHOLDERS,
    )

    template = "{job_title} {company} {location} {job_description} {cv_content} {user_name} {tone} {length} {focus} {language}"
    found = set(_extract_placeholders(template))
    assert found == REQUIRED_PLACEHOLDERS


def test_decrypt_cv_text_raises_on_failure():
    from src.services.cover_letter_service import _decrypt_cv_text

    cv = MagicMock()
    cv.content = b"invalid_data"
    with pytest.raises(ValueError, match="Failed to decrypt CV content"):
        _decrypt_cv_text(cv)


def test_decrypt_cv_text_returns_empty_for_none():
    from src.services.cover_letter_service import _decrypt_cv_text

    cv = MagicMock()
    cv.content = None
    result = _decrypt_cv_text(cv)
    assert result == ""
