import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.user_cv import UserCV
from src.repositories.base import AbstractRepository
from src.utils.encryption import encrypt_data, decrypt_data


class CVRepository(AbstractRepository[UserCV]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, UserCV)

    async def get_by_user_id(self, user_id: uuid.UUID) -> list[UserCV]:
        stmt = (
            select(UserCV)
            .where(UserCV.user_id == user_id, UserCV.deleted_at.is_(None))
            .order_by(UserCV.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_active_cv(self, user_id: uuid.UUID) -> Optional[UserCV]:
        stmt = select(UserCV).where(
            UserCV.user_id == user_id,
            UserCV.is_active,
            UserCV.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_active_cvs(self, user_id: uuid.UUID) -> list[UserCV]:
        stmt = select(UserCV).where(
            UserCV.user_id == user_id,
            UserCV.is_active,
            UserCV.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def count_by_user(self, user_id: uuid.UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(UserCV)
            .where(
                UserCV.user_id == user_id,
                UserCV.deleted_at.is_(None),
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def count_active_by_user(self, user_id: uuid.UUID) -> int:
        stmt = (
            select(func.count())
            .select_from(UserCV)
            .where(
                UserCV.user_id == user_id,
                UserCV.is_active,
                UserCV.deleted_at.is_(None),
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one()

    async def create_cv(
        self,
        user_id: uuid.UUID,
        title: str,
        content: str,
        embedding_vector: Optional[list[float]] = None,
        is_active: bool = True,
    ) -> UserCV:
        encrypted_content = encrypt_data(content).encode("utf-8")
        return await self.create(
            user_id=user_id,
            title=title,
            content=encrypted_content,
            embedding_vector=embedding_vector,
            is_active=is_active,
        )

    def decrypt_content(self, cv: UserCV) -> str:
        return decrypt_data(cv.content.decode("utf-8"))

    async def set_active_cv(
        self, cv_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[UserCV]:
        stmt = select(UserCV).where(
            UserCV.id == cv_id,
            UserCV.user_id == user_id,
            UserCV.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        cv = result.scalar_one_or_none()

        if not cv:
            return None

        await self._session.execute(
            update(UserCV).where(UserCV.user_id == user_id).values(is_active=False)
        )

        cv.is_active = True
        await self._session.flush()
        return cv

    async def deactivate_cv(
        self, cv_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[UserCV]:
        stmt = select(UserCV).where(
            UserCV.id == cv_id,
            UserCV.user_id == user_id,
            UserCV.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        cv = result.scalar_one_or_none()

        if not cv:
            return None

        cv.is_active = False
        await self._session.flush()
        return cv

    async def soft_delete_cv(
        self, cv_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[UserCV]:
        stmt = select(UserCV).where(
            UserCV.id == cv_id,
            UserCV.user_id == user_id,
            UserCV.deleted_at.is_(None),
        )
        result = await self._session.execute(stmt)
        cv = result.scalar_one_or_none()

        if not cv:
            return None

        cv.is_active = False
        cv.deleted_at = datetime.utcnow()
        await self._session.flush()
        return cv

    async def update_embedding(
        self,
        cv_id: uuid.UUID,
        embedding_vector: list[float],
    ) -> Optional[UserCV]:
        return await self.update(cv_id, embedding_vector=embedding_vector)

    async def update_evaluation(
        self,
        cv_id: uuid.UUID,
        skills: list[str],
        experience_summary: str,
        completeness_score: Decimal,
        improvement_suggestions: list[str],
    ) -> Optional[UserCV]:
        return await self.update(
            cv_id,
            skills=skills,
            experience_summary=experience_summary,
            completeness_score=completeness_score,
            improvement_suggestions=improvement_suggestions,
            evaluated_at=datetime.utcnow(),
        )

    async def get_all_for_reencryption(self, batch_size: int = 100) -> list[UserCV]:
        stmt = select(UserCV).where(UserCV.deleted_at.is_(None)).limit(batch_size)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())
