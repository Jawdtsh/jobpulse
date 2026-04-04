import pytest
import pytest_asyncio
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from src.repositories.user_repository import UserRepository
from src.repositories.cv_repository import CVRepository


@pytest_asyncio.fixture
async def user_repo(async_session: AsyncSession):
    return UserRepository(async_session)


@pytest_asyncio.fixture
async def cv_repo(async_session: AsyncSession):
    return CVRepository(async_session)


@pytest_asyncio.fixture
async def test_user(user_repo: UserRepository):
    return await user_repo.create_user(
        telegram_id=123456789,
        first_name="Test",
        last_name="User",
    )


class TestCVRepository:
    @pytest.mark.asyncio
    async def test_create_cv(self, cv_repo: CVRepository, test_user):
        cv = await cv_repo.create_cv(
            user_id=test_user.id,
            title="My Resume",
            content="This is my CV content",
        )
        assert cv.title == "My Resume"
        assert cv.content != b"This is my CV content"
        assert cv.is_active

    @pytest.mark.asyncio
    async def test_decrypt_cv_content(self, cv_repo: CVRepository, test_user):
        original_content = "Secret CV data"
        cv = await cv_repo.create_cv(
            user_id=test_user.id,
            title="Encrypted CV",
            content=original_content,
        )
        decrypted = cv_repo.decrypt_content(cv)
        assert decrypted == original_content

    @pytest.mark.asyncio
    async def test_get_by_user_id(self, cv_repo: CVRepository, test_user):
        await cv_repo.create_cv(
            user_id=test_user.id,
            title="CV 1",
            content="Content 1",
        )
        await cv_repo.create_cv(
            user_id=test_user.id,
            title="CV 2",
            content="Content 2",
        )
        cvs = await cv_repo.get_by_user_id(test_user.id)
        assert len(cvs) == 2

    @pytest.mark.asyncio
    async def test_get_active_cv(self, cv_repo: CVRepository, test_user):
        cv1 = await cv_repo.create_cv(
            user_id=test_user.id,
            title="Inactive CV",
            content="Content",
            is_active=False,
        )
        cv2 = await cv_repo.create_cv(
            user_id=test_user.id,
            title="Active CV",
            content="Content",
            is_active=True,
        )
        active = await cv_repo.get_active_cv(test_user.id)
        assert active is not None
        assert active.id == cv2.id

    @pytest.mark.asyncio
    async def test_update_embedding(self, cv_repo: CVRepository, test_user):
        cv = await cv_repo.create_cv(
            user_id=test_user.id,
            title="CV with embedding",
            content="Content",
        )
        embedding = [0.1] * 768
        updated = await cv_repo.update_embedding(cv.id, embedding)
        assert updated is not None
        assert updated.embedding_vector is not None

    @pytest.mark.asyncio
    async def test_set_active_cv(self, cv_repo: CVRepository, test_user):
        cv1 = await cv_repo.create_cv(
            user_id=test_user.id,
            title="CV 1",
            content="Content 1",
            is_active=True,
        )
        cv2 = await cv_repo.create_cv(
            user_id=test_user.id,
            title="CV 2",
            content="Content 2",
            is_active=False,
        )
        await cv_repo.set_active_cv(cv2.id, test_user.id)
        updated_cv1 = await cv_repo.get(cv1.id)
        updated_cv2 = await cv_repo.get(cv2.id)
        assert not updated_cv1.is_active
        assert updated_cv2.is_active
