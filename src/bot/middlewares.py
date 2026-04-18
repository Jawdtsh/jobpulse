import logging
import time

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery
from cachetools import TTLCache

logger = logging.getLogger(__name__)


class AuthMiddleware(BaseMiddleware):
    async def __call__(self, handler, event, data):
        user = getattr(event, "from_user", None)
        if user is None:
            return await handler(event, data)

        from src.database import get_async_session
        from src.repositories.user_repository import UserRepository

        async for session in get_async_session():
            user_repo = UserRepository(session)
            db_user = await user_repo.get_by_telegram_id(user.id)
            data["db_user"] = db_user
            break

        return await handler(event, data)


class RateLimiterMiddleware(BaseMiddleware):
    def __init__(self, rate_limit: int = 30):
        self._rate_limit = rate_limit
        self._user_timestamps: TTLCache = TTLCache(maxsize=10000, ttl=60)

    async def __call__(self, handler, event, data):
        user = getattr(event, "from_user", None)
        if user is None:
            return await handler(event, data)

        now = time.monotonic()
        timestamps = self._user_timestamps.get(user.id, [])
        timestamps = [t for t in timestamps if now - t < 1.0]

        if len(timestamps) >= self._rate_limit:
            if isinstance(event, CallbackQuery):
                await event.answer(
                    "يرجى الانتظار... (Please wait...)", show_alert=False
                )
            return None

        timestamps.append(now)
        self._user_timestamps[user.id] = timestamps
        return await handler(event, data)
