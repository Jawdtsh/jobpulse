import logging
from typing import Optional

from telethon import TelegramClient
from telethon.errors import (
    ChannelPrivateError,
    ChannelInvalidError,
    FloodWaitError,
)
from telethon.sessions import StringSession

from src.services.exceptions import ChannelInaccessibleError

logger = logging.getLogger(__name__)


class TelegramScraperService:
    def __init__(self) -> None:
        self._client: Optional[TelegramClient] = None

    async def connect_session(
        self,
        session_string: str,
        api_id: int,
        api_hash: str,
    ) -> TelegramClient:
        if self._client is not None:
            try:
                await self._client.disconnect()
            except Exception:
                pass

        self._client = TelegramClient(
            StringSession(session_string),
            api_id,
            api_hash,
        )
        await self._client.connect()
        return self._client

    async def fetch_messages(
        self,
        channel_username: str,
        batch_size: int = 100,
        after_message_id: Optional[int] = None,
    ) -> list[dict]:
        if self._client is None:
            raise RuntimeError("Client not connected")

        messages = []
        try:
            async for msg in self._client.iter_messages(
                channel_username,
                limit=batch_size,
                min_id=after_message_id or 0,
            ):
                text = self.extract_text(msg)
                if text:
                    messages.append({"id": msg.id, "text": text, "date": msg.date})
        except FloodWaitError as e:
            logger.warning("FloodWaitError: %s", e.seconds)
            raise
        except (ChannelPrivateError, ChannelInvalidError) as e:
            logger.error("Channel inaccessible: %s - %s", channel_username, e)
            raise ChannelInaccessibleError(channel_username, str(e))

        return messages

    def extract_text(self, message) -> Optional[str]:
        if message is None:
            return None
        if not hasattr(message, "text") or not message.text:
            return None
        return message.text

    async def disconnect(self) -> None:
        if self._client is not None:
            try:
                await self._client.disconnect()
            except Exception:
                pass
            self._client = None
