import logging
from datetime import datetime, timezone
from typing import Optional

from telethon import TelegramClient

from config.settings import get_settings

logger = logging.getLogger(__name__)


class AdminAlertService:
    def __init__(
        self,
        scraper_service: Optional[object] = None,
    ) -> None:
        self._scraper_service = scraper_service

    async def send_alert(self, error_type: str, details: dict) -> None:
        settings = get_settings()
        channel_id = settings.telegram.admin_alert_channel_id
        if not channel_id:
            logger.warning("admin_alert_channel_id not configured, skipping alert")
            return

        message = self._format_message(error_type, details)
        try:
            client = TelegramClient(
                "admin_alert_session",
                settings.telegram.telethon_api_id,
                settings.telegram.telethon_api_hash,
            )
            await client.connect()
            try:
                await client.sign_in(bot_token=settings.telegram.bot_token)
                await client.send_message(int(channel_id), message)
            finally:
                await client.disconnect()
        except Exception as e:
            logger.exception("Failed to send admin alert", exc_info=e)

    def _format_message(self, error_type: str, details: dict) -> str:
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        lines = [
            "**JobPulse Alert**",
            f"Type: `{error_type}`",
            f"Time: {timestamp}",
        ]
        for key, value in details.items():
            lines.append(f"{key}: `{value}`")
        return "\n".join(lines)
