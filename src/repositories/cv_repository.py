import uuid
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.user_cv import UserCV
from src.repositories.base import AbstractRepository
from src.utils.encryption import encrypt_data, decrypt_data


class CVRepository(AbstractRepository[UserCV]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, UserCV)

    async def get_by_user_id(self, user_id: uuid.UUID) -> list[UserCV]:
        stmt = select(UserCV).where(UserCV.user_id == user_id)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_active_cv(self, user_id: uuid.UUID) -> Optional[UserCV]:
        stmt = select(UserCV).where(
            UserCV.user_id == user_id,
            UserCV.is_active == True,
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_cv(
        self,
        user_id: uuid.UUID,
        title: str,
        content: str,
        embedding_vector: Optional[list[float]] = None,
        is_active: bool = True,
    ) -> UserCV:
        encrypted_content = encrypt_data(content)
        return await self.create(
            user_id=user_id,
            title=title,
            content=encrypted_content,
            embedding_vector=embedding_vector,
            is_active=is_active,
        )

    def decrypt_content(self, cv: UserCV) -> str:
        return decrypt_data(cv.content)

    async def set_active_cv(
        self, cv_id: uuid.UUID, user_id: uuid.UUID
    ) -> Optional[UserCV]:
        user_cvs = await self.get_by_user_id(user_id)
        for cv in user_cvs:
            cv.is_active = cv.id == cv_id
        await self._session.flush()
        return await self.get(cv_id)

    async def update_embedding(
        self,
        cv_id: uuid.UUID,
        embedding_vector: list[float],
    ) -> Optional[UserCV]:
        return await self.update(cv_id, embedding_vector=embedding_vector)
