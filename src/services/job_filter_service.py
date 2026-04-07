import json
import logging
from typing import Any, Optional

import redis.asyncio as aioredis

from config.settings import get_settings, Settings
from src.repositories.spam_rule_repository import SpamRuleRepository

logger = logging.getLogger(__name__)

_CACHE_KEY = "spam_rules:all"
_CACHE_TTL = 300
_MIN_LENGTH = 50


class JobFilterService:
    def __init__(self, spam_rule_repo: SpamRuleRepository) -> None:
        self._spam_rule_repo = spam_rule_repo
        self._rules_cache: Optional[list[dict[str, Any]]] = None
        self._redis: aioredis.Redis | None = None
        self._settings: Settings = get_settings()

    def _get_redis(self) -> aioredis.Redis:
        if self._redis is None:
            self._redis = aioredis.from_url(
                self._settings.redis.redis_url, decode_responses=True
            )
        return self._redis

    async def filter_message(self, text: str) -> bool:
        if not text or not text.strip():
            return False
        text_lower = text.lower()
        rules = await self._get_rules()
        for rule in rules:
            if rule["pattern"].lower() in text_lower:
                return False
        if len(text.strip()) < _MIN_LENGTH:
            return False
        return True

    async def _get_rules(self) -> list[dict[str, Any]]:
        redis = self._get_redis()
        try:
            cached = await redis.get(_CACHE_KEY)
            if cached:
                return json.loads(cached)
        except Exception:
            logger.warning("Redis cache read failed, falling back to DB")

        try:
            active_rules = await self._spam_rule_repo.get_active_rules()
            rules = [
                {"pattern": r.pattern, "rule_type": r.rule_type} for r in active_rules
            ]
        except Exception:
            logger.exception("Failed to load spam rules from DB")
            return []

        try:
            await redis.setex(_CACHE_KEY, _CACHE_TTL, json.dumps(rules))
        except Exception:
            logger.warning("Failed to cache spam rules in Redis")

        return rules
