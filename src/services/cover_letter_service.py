import logging
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession

from config.settings import get_settings
from src.repositories.cover_letter_repository import CoverLetterRepository

logger = logging.getLogger(__name__)

REQUIRED_PLACEHOLDERS = {
    "job_title",
    "company",
    "location",
    "job_description",
    "cv_content",
    "user_name",
    "tone",
    "length",
    "focus",
    "language",
}

LENGTH_WORD_COUNTS = {
    "short": 200,
    "medium": 400,
    "long": 600,
}

LENGTH_LABELS = {
    "short": "short (around 200 words)",
    "medium": "medium (around 400 words)",
    "long": "long (around 600 words)",
}

VALID_TONES = {"formal", "casual", "professional"}
VALID_LENGTHS = {"short", "medium", "long"}
VALID_FOCUSES = {"skills", "experience", "education", "all"}
VALID_LANGUAGES = {"arabic", "english", "bilingual"}

DEFAULT_PROMPT = (
    "Write a {length} cover letter in {language} with a {tone} tone.\n"
    "Focus on: {focus}\n\n"
    "Job Details:\n"
    "- Position: {job_title}\n"
    "- Company: {company}\n"
    "- Location: {location}\n"
    "- Description: {job_description}\n\n"
    "My Background:\n{cv_content}\n\n"
    "Name: {user_name}"
)


class CoverLetterService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = CoverLetterRepository(session)
        self._prompt_template = self._load_prompt_template()

    def _load_prompt_template(self) -> str:
        settings = get_settings()
        path = Path(settings.cover_letter.prompt_path)
        if not path.exists():
            logger.error("Prompt template not found at %s, using default", path)
            return DEFAULT_PROMPT
        content = path.read_text(encoding="utf-8")
        missing = REQUIRED_PLACEHOLDERS - set(
            p[1:-1] for p in _extract_placeholders(content)
        )
        if missing:
            logger.error(
                "Prompt template missing placeholders: %s, using default",
                missing,
            )
            return DEFAULT_PROMPT
        return content

    async def generate(
        self,
        user_id,
        job_id,
        cv_id,
        job_title: str,
        company: str,
        location: str,
        job_description: str,
        cv_content: str,
        user_name: str,
        tone: str = "professional",
        length: str = "medium",
        focus: str = "all",
        language: str = "english",
        ai_model: str = "",
    ) -> str:
        from src.services.ai_provider_service import AIProviderService

        self._validate_options(tone, length, focus, language)
        prompt = self._build_prompt(
            job_title=job_title,
            company=company,
            location=location,
            job_description=job_description,
            cv_content=cv_content,
            user_name=user_name,
            tone=tone,
            length=LENGTH_LABELS.get(length, length),
            focus=focus,
            language=language,
            word_count=LENGTH_WORD_COUNTS.get(length, 400),
        )

        settings = get_settings()
        if not ai_model:
            ai_model = settings.cover_letter.model_name

        ai_service = AIProviderService()
        content = await ai_service.call_model(
            model_type="extractor",
            prompt=prompt,
            timeout=settings.cover_letter.generation_timeout,
        )

        max_len = settings.cover_letter.max_content_length
        if len(content) > max_len:
            content = content[:max_len]

        await self._repo.create_log(
            user_id=user_id,
            job_id=job_id,
            cv_id=cv_id,
            content=content,
            tone=tone,
            length=length,
            focus_area=focus,
            language=language,
            ai_model=ai_model,
            generation_count=1,
            counted_in_quota=True,
        )
        return content

    async def regenerate(
        self,
        cover_letter_id,
        user_id,
        tone: str | None = None,
        length: str | None = None,
        focus: str | None = None,
        language: str | None = None,
    ) -> str | None:
        from src.services.ai_provider_service import AIProviderService

        record = await self._repo.get_by_id(cover_letter_id)
        if record is None or record.user_id != user_id:
            return None

        new_tone = tone or record.tone
        new_length = length or record.length
        new_focus = focus or record.focus_area
        new_language = language or record.language

        self._validate_options(new_tone, new_length, new_focus, new_language)

        prompt = self._build_prompt(
            job_title="",
            company="",
            location="",
            job_description="",
            cv_content="",
            user_name="",
            tone=new_tone,
            length=LENGTH_LABELS.get(new_length, new_length),
            focus=new_focus,
            language=new_language,
            word_count=LENGTH_WORD_COUNTS.get(new_length, 400),
        )

        settings = get_settings()
        ai_model = record.ai_model or settings.cover_letter.model_name
        ai_service = AIProviderService()
        content = await ai_service.call_model(
            model_type="extractor",
            prompt=prompt,
            timeout=settings.cover_letter.generation_timeout,
        )

        max_len = settings.cover_letter.max_content_length
        if len(content) > max_len:
            content = content[:max_len]

        await self._repo.create_log(
            user_id=user_id,
            job_id=record.job_id,
            cv_id=record.cv_id,
            content=content,
            tone=new_tone,
            length=new_length,
            focus_area=new_focus,
            language=new_language,
            ai_model=ai_model,
            generation_count=record.generation_count + 1,
            counted_in_quota=True,
        )
        return content

    async def get_latest(self, user_id, job_id):
        return await self._repo.get_latest_for_job(user_id, job_id)

    async def get_by_id(self, cover_letter_id):
        return await self._repo.get_by_id(cover_letter_id)

    def _build_prompt(self, **kwargs) -> str:
        try:
            return self._prompt_template.format(**kwargs)
        except KeyError as exc:
            logger.error("Prompt placeholder error: %s", exc)
            return DEFAULT_PROMPT.format(**kwargs)

    @staticmethod
    def _validate_options(tone: str, length: str, focus: str, language: str) -> None:
        if tone not in VALID_TONES:
            raise ValueError(f"Invalid tone: {tone}")
        if length not in VALID_LENGTHS:
            raise ValueError(f"Invalid length: {length}")
        if focus not in VALID_FOCUSES:
            raise ValueError(f"Invalid focus: {focus}")
        if language not in VALID_LANGUAGES:
            raise ValueError(f"Invalid language: {language}")

    @staticmethod
    def check_cv_completeness(cv) -> tuple[bool, float]:
        if cv is None:
            return False, 0.0
        score = float(cv.completeness_score or 0)
        return score >= 60.0, score


def _extract_placeholders(template: str) -> list[str]:
    import re

    return re.findall(r"\{(\w+)\}", template)
