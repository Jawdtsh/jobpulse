import json
import logging
from datetime import datetime, timezone
from typing import Any

import redis.asyncio as aioredis

from config.settings import get_settings

logger = logging.getLogger(__name__)

SESSION_PREFIX = "bot_session:"
SESSION_TTL = 600
CLEANUP_THRESHOLD = SESSION_TTL + 300


class BotSessionService:
    def __init__(self) -> None:
        self._redis: aioredis.Redis | None = None

    def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            settings = get_settings()
            self._redis = aioredis.from_url(
                settings.redis.redis_url, decode_responses=True
            )
        return self._redis

    def _key(self, user_id: int) -> str:
        return f"{SESSION_PREFIX}{user_id}"

    async def get_session(self, user_id: int) -> dict[str, Any] | None:
        try:
            redis = self._get_redis()
            data = await redis.get(self._key(user_id))
            if data is None:
                return None
            return json.loads(data)
        except Exception:
            logger.exception("Failed to get session for user %s", user_id)
            return None

    async def set_session(
        self, user_id: int, state: str, flow_data: dict[str, Any] | None = None
    ) -> None:
        try:
            redis = self._get_redis()
            session_data = {
                "user_id": user_id,
                "current_state": state,
                "last_activity": datetime.now(timezone.utc).isoformat(),
                "flow_data": flow_data or {},
            }
            await redis.set(
                self._key(user_id), json.dumps(session_data), ex=SESSION_TTL
            )
        except Exception:
            logger.exception("Failed to set session for user %s", user_id)

    async def update_activity(self, user_id: int) -> None:
        session = await self.get_session(user_id)
        if session:
            await self.set_session(
                user_id, session["current_state"], session.get("flow_data")
            )

    async def clear_session(self, user_id: int) -> None:
        try:
            redis = self._get_redis()
            await redis.delete(self._key(user_id))
        except Exception:
            logger.exception("Failed to clear session for user %s", user_id)

    async def is_expired(self, user_id: int) -> bool:
        session = await self.get_session(user_id)
        if session is None:
            return True
        last_activity = datetime.fromisoformat(session["last_activity"])
        elapsed = (datetime.now(timezone.utc) - last_activity).total_seconds()
        return elapsed > SESSION_TTL

    async def cleanup_expired_sessions(self) -> int:
        try:
            redis = self._get_redis()
            pattern = f"{SESSION_PREFIX}*"
            keys = []
            async for key in redis.scan_iter(match=pattern):
                keys.append(key)
            cleaned = 0
            for key in keys:
                data = await redis.get(key)
                if data:
                    session = json.loads(data)
                    last_activity = datetime.fromisoformat(session["last_activity"])
                    elapsed = (
                        datetime.now(timezone.utc) - last_activity
                    ).total_seconds()
                    if elapsed > CLEANUP_THRESHOLD:
                        await redis.delete(key)
                        cleaned += 1
            return cleaned
        except Exception:
            logger.exception("Failed to cleanup expired sessions")
            return 0
