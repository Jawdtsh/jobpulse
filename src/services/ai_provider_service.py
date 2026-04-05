import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

import google.generativeai as genai
import redis.asyncio as aioredis
from openai import AsyncOpenAI

from config.ai_models import (
    ACTIVE_MODELS,
    API_PROVIDERS,
    DAILY_LIMITS,
    FALLBACK_CHAIN,
    PROVIDER_BASE_URLS,
)
from config.settings import get_settings
from src.services.exceptions import (
    AIServiceUnavailableError,
    DailyLimitReachedError,
    InvalidEmbeddingDimensionsError,
    InvalidModelTypeError,
)

logger = logging.getLogger(__name__)

_REDIS_KEY_TPL = "ai_daily_usage:{model}:{date}"
_DAILY_TTL = 86400


def _today() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _get_redis() -> aioredis.Redis:
    settings = get_settings()
    return aioredis.from_url(
        settings.redis.redis_url,
        decode_responses=True,
    )


class AIProviderService:
    def __init__(self) -> None:
        self._settings = get_settings()
        self._clients: dict[str, AsyncOpenAI] = {}

    def _get_openai_client(self, provider: str) -> AsyncOpenAI:
        if provider in self._clients:
            return self._clients[provider]
        base_url = PROVIDER_BASE_URLS.get(provider)
        key_env = {
            "groq": self._settings.ai.groq_api_key,
            "openrouter": self._settings.ai.openrouter_api_key,
            "zhipu": self._settings.ai.zhipu_api_key,
        }
        api_key = key_env.get(provider, "")
        client = AsyncOpenAI(base_url=base_url, api_key=api_key)
        self._clients[provider] = client
        return client

    async def call_model(
        self,
        model_type: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        response_format: Optional[dict] = None,
        timeout: int = 30,
    ) -> str:
        if model_type not in ACTIVE_MODELS:
            raise InvalidModelTypeError(model_type)

        chain = FALLBACK_CHAIN.get(model_type, [])
        if not chain:
            raise AIServiceUnavailableError(
                f"No fallback chain for model_type: {model_type}"
            )

        for model_name in chain:
            if model_name == "regex_only":
                continue
            provider_info = API_PROVIDERS.get(model_name)
            if not provider_info:
                continue

            if not await self.check_daily_limit(model_name):
                raise DailyLimitReachedError(model_name)

            for attempt in range(3):
                try:
                    result = await self._call_provider(
                        model_name=model_name,
                        provider_info=provider_info,
                        prompt=prompt,
                        system_prompt=system_prompt,
                        response_format=response_format,
                        timeout=timeout,
                    )
                    await self.increment_usage(model_name)
                    return result
                except Exception as exc:
                    backoff = 2**attempt
                    logger.warning(
                        "AI call failed model=%s attempt=%d: %s",
                        model_name,
                        attempt + 1,
                        exc,
                    )
                    if attempt < 2:
                        await asyncio.sleep(backoff)

        raise AIServiceUnavailableError(
            f"All providers failed for model_type: {model_type}"
        )

    async def _call_provider(
        self,
        model_name: str,
        provider_info: dict,
        prompt: str,
        system_prompt: Optional[str] = None,
        response_format: Optional[dict] = None,
        timeout: int = 30,
    ) -> str:
        provider = provider_info["provider"]

        if provider == "google":
            return await self._call_google(
                model_name, prompt, system_prompt, response_format, timeout
            )

        client = self._get_openai_client(provider)
        kwargs: dict = {
            "model": model_name,
            "messages": [],
            "timeout": timeout,
        }
        if system_prompt:
            kwargs["messages"].append({"role": "system", "content": system_prompt})
        kwargs["messages"].append({"role": "user", "content": prompt})
        if response_format:
            kwargs["response_format"] = {"type": "json_object"}

        resp = await client.chat.completions.create(**kwargs)
        return resp.choices[0].message.content or ""

    async def _call_google(
        self,
        model_name: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        response_format: Optional[dict] = None,
        timeout: int = 30,
    ) -> str:
        genai.configure(api_key=self._settings.ai.gemini_api_key)
        generation_config = {}
        if response_format:
            generation_config["response_mime_type"] = "application/json"
        model = genai.GenerativeModel(
            model_name,
            system_instruction=system_prompt,
            generation_config=generation_config,
        )
        result = await asyncio.wait_for(
            asyncio.to_thread(model.generate_content, prompt),
            timeout=timeout,
        )
        return result.text or ""

    async def generate_embedding(
        self,
        text: str,
        expected_dimensions: int = 768,
    ) -> Optional[list[float]]:
        chain = FALLBACK_CHAIN.get("embedder", [])
        for model_name in chain:
            for attempt in range(3):
                try:
                    provider_info = API_PROVIDERS.get(model_name)
                    if not provider_info:
                        continue

                    if provider_info["provider"] == "google":
                        embedding = await self._google_embedding(model_name, text)
                    else:
                        embedding = await self._openai_embedding(
                            model_name, provider_info, text
                        )

                    if len(embedding) != expected_dimensions:
                        raise InvalidEmbeddingDimensionsError(
                            expected_dimensions, len(embedding)
                        )
                    await self.increment_usage(model_name)
                    return embedding
                except InvalidEmbeddingDimensionsError:
                    logger.warning(
                        "Embedding dim mismatch model=%s attempt=%d",
                        model_name,
                        attempt + 1,
                    )
                except Exception as exc:
                    logger.warning(
                        "Embedding failed model=%s attempt=%d: %s",
                        model_name,
                        attempt + 1,
                        exc,
                    )
                if attempt < 2:
                    await asyncio.sleep(2**attempt)
        return None

    async def _google_embedding(self, model_name: str, text: str) -> list[float]:
        genai.configure(api_key=self._settings.ai.gemini_api_key)
        result = await asyncio.to_thread(
            genai.embed_content, model=model_name, content=text
        )
        return result["embedding"]

    async def _openai_embedding(
        self, model_name: str, provider_info: dict, text: str
    ) -> list[float]:
        client = self._get_openai_client(provider_info["provider"])
        resp = await client.embeddings.create(model=model_name, input=text)
        return resp.data[0].embedding

    async def check_daily_limit(self, model_name: str) -> bool:
        limits = DAILY_LIMITS.get(model_name)
        if not limits or limits.get("rpd") is None:
            return True
        rpd = limits["rpd"]
        redis = _get_redis()
        key = _REDIS_KEY_TPL.format(model=model_name, date=_today())
        try:
            current = await redis.get(key)
            if current is not None and int(current) >= rpd:
                return False
        finally:
            await redis.close()
        return True

    async def increment_usage(self, model_name: str) -> int:
        redis = _get_redis()
        key = _REDIS_KEY_TPL.format(model=model_name, date=_today())
        try:
            count = await redis.incr(key)
            if count == 1:
                await redis.expire(key, _DAILY_TTL)
            return count
        finally:
            await redis.close()
