import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import select, and_, update
from sqlalchemy.ext.asyncio import AsyncSession
from src.models.telegram_session import TelegramSession
from src.repositories.base import AbstractRepository
from src.utils.encryption import encrypt_data, decrypt_data


class TelegramSessionRepository(AbstractRepository[TelegramSession]):
    def __init__(self, session: AsyncSession):
        super().__init__(session, TelegramSession)

    async def get_available_sessions(self) -> list[TelegramSession]:
        stmt = (
            select(TelegramSession)
            .where(
                and_(
                    TelegramSession.is_active == True,
                    TelegramSession.is_banned == False,
                )
            )
            .order_by(
                TelegramSession.use_count.asc(),
                TelegramSession.last_used_at.asc().nulls_first(),
            )
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_next_session(self) -> Optional[TelegramSession]:
        sessions = await self.get_available_sessions()
        return sessions[0] if sessions else None

    async def create_session(
        self,
        session_string: str,
        phone_number: str,
    ) -> TelegramSession:
        encrypted_session = encrypt_data(session_string)
        return await self.create(
            session_string=encrypted_session,
            phone_number=phone_number,
        )

    def decrypt_session(self, session: TelegramSession) -> str:
        return decrypt_data(session.session_string)

    async def mark_used(self, session_id: uuid.UUID) -> Optional[TelegramSession]:
        # Use atomic DB-side increment to prevent race conditions
        stmt = (
            update(TelegramSession)
            .where(TelegramSession.id == session_id)
            .values(
                use_count=TelegramSession.use_count + 1, last_used_at=datetime.utcnow()
            )
            .returning(TelegramSession)
        )
        result = await self._session.execute(stmt)
        await self._session.flush()
        return result.scalar_one_or_none()

    async def mark_banned(
        self,
        session_id: uuid.UUID,
        reason: Optional[str] = None,
    ) -> Optional[TelegramSession]:
        return await self.update(
            session_id,
            is_banned=True,
            ban_reason=reason,
        )

    async def deactivate(self, session_id: uuid.UUID) -> Optional[TelegramSession]:
        return await self.update(session_id, is_active=False)

    async def activate(self, session_id: uuid.UUID) -> Optional[TelegramSession]:
        return await self.update(session_id, is_active=True)

    async def get_by_phone(self, phone_number: str) -> Optional[TelegramSession]:
        stmt = select(TelegramSession).where(
            TelegramSession.phone_number == phone_number
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()
