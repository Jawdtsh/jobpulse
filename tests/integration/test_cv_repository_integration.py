import uuid

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import User
from src.repositories.cv_repository import CVRepository


@pytest_asyncio.fixture
async def user_id(async_session: AsyncSession) -> uuid.UUID:
    user = User(
        telegram_id=123456789,
        first_name="Test",
        last_name="User",
        referral_code="testrefcode1",
        subscription_tier="free",
    )
    async_session.add(user)
    await async_session.flush()
    return user.id


@pytest_asyncio.fixture
def cv_repo(async_session: AsyncSession) -> CVRepository:
    return CVRepository(async_session)


class TestCVRepository:
    @pytest.mark.asyncio
    async def test_create_cv(self, cv_repo: CVRepository, user_id: uuid.UUID):
        cv = await cv_repo.create_cv(
            user_id=user_id,
            title="Test CV",
            content="This is my CV content for testing purposes with enough text.",
        )
        assert cv.id is not None
        assert cv.title == "Test CV"
        assert cv.is_active is True

    @pytest.mark.asyncio
    async def test_get_by_user_id(self, cv_repo: CVRepository, user_id: uuid.UUID):
        await cv_repo.create_cv(
            user_id=user_id, title="CV 1", content="Content one here."
        )
        await cv_repo.create_cv(
            user_id=user_id, title="CV 2", content="Content two here."
        )

        cvs = await cv_repo.get_by_user_id(user_id)
        assert len(cvs) == 2

    @pytest.mark.asyncio
    async def test_get_active_cv(self, cv_repo: CVRepository, user_id: uuid.UUID):
        await cv_repo.create_cv(
            user_id=user_id,
            title="Active CV",
            content="Active content here.",
            is_active=True,
        )
        await cv_repo.create_cv(
            user_id=user_id,
            title="Inactive CV",
            content="Inactive content here.",
            is_active=False,
        )

        active = await cv_repo.get_active_cv(user_id)
        assert active is not None
        assert active.title == "Active CV"

    @pytest.mark.asyncio
    async def test_set_active_cv(self, cv_repo: CVRepository, user_id: uuid.UUID):
        await cv_repo.create_cv(
            user_id=user_id, title="CV 1", content="First CV content.", is_active=True
        )
        cv2 = await cv_repo.create_cv(
            user_id=user_id, title="CV 2", content="Second CV content.", is_active=False
        )

        result = await cv_repo.set_active_cv(cv2.id, user_id)
        assert result is not None
        assert result.is_active is True

    @pytest.mark.asyncio
    async def test_count_by_user(self, cv_repo: CVRepository, user_id: uuid.UUID):
        await cv_repo.create_cv(user_id=user_id, title="CV 1", content="Content one.")
        await cv_repo.create_cv(user_id=user_id, title="CV 2", content="Content two.")

        count = await cv_repo.count_by_user(user_id)
        assert count == 2

    @pytest.mark.asyncio
    async def test_soft_delete_cv(self, cv_repo: CVRepository, user_id: uuid.UUID):
        cv = await cv_repo.create_cv(
            user_id=user_id, title="CV to delete", content="Delete this CV."
        )
        result = await cv_repo.soft_delete_cv(cv.id, user_id)
        assert result is not None
        assert result.deleted_at is not None
        assert result.is_active is False

    @pytest.mark.asyncio
    async def test_decrypt_content(self, cv_repo: CVRepository, user_id: uuid.UUID):
        original = "This is my encrypted CV content for testing."
        cv = await cv_repo.create_cv(
            user_id=user_id, title="Encrypted CV", content=original
        )
        decrypted = cv_repo.decrypt_content(cv)
        assert decrypted == original

    @pytest.mark.asyncio
    async def test_update_evaluation(self, cv_repo: CVRepository, user_id: uuid.UUID):
        from decimal import Decimal

        cv = await cv_repo.create_cv(
            user_id=user_id, title="Eval CV", content="Content for evaluation testing."
        )
        updated = await cv_repo.update_evaluation(
            cv_id=cv.id,
            skills=["Python", "FastAPI"],
            experience_summary="5 years experience",
            completeness_score=Decimal("85.50"),
            improvement_suggestions=["Add more details"],
        )
        assert updated is not None
        assert updated.skills == ["Python", "FastAPI"]
        assert updated.experience_summary == "5 years experience"
        assert updated.completeness_score == Decimal("85.50")
        assert updated.evaluated_at is not None

    @pytest.mark.asyncio
    async def test_deleted_cvs_excluded_from_list(
        self, cv_repo: CVRepository, user_id: uuid.UUID
    ):
        await cv_repo.create_cv(
            user_id=user_id, title="Active CV", content="Active content."
        )
        cv2 = await cv_repo.create_cv(
            user_id=user_id, title="Delete me", content="To be deleted."
        )
        await cv_repo.soft_delete_cv(cv2.id, user_id)

        cvs = await cv_repo.get_by_user_id(user_id)
        assert len(cvs) == 1
        assert cvs[0].title == "Active CV"
