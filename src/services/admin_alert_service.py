import logging
from datetime import datetime, timezone

from telethon import TelegramClient
from telethon.sessions import StringSession

from config.settings import get_settings

logger = logging.getLogger(__name__)


class AdminAlertService:
    async def send_alert(self, error_type: str, details: dict) -> None:
        settings = get_settings()
        channel_id = settings.telegram.admin_alert_channel_id
        if not channel_id:
            logger.warning("admin_alert_channel_id not configured, skipping alert")
            return

        message = self._format_message(error_type, details)
        try:
            client = TelegramClient(
                StringSession(),
                settings.telegram.telethon_api_id,
                settings.telegram.telethon_api_hash,
            )
            await client.connect()
            try:
                await client.send_message(int(channel_id), message)
            finally:
                await client.disconnect()
        except Exception as e:
            logger.error("Failed to send admin alert: %s", e)

    def _format_message(self, error_type: str, details: dict) -> str:
        ts = datetime.now(timezone.utc).isoformat()
        lines = [f"**ALERT: {error_type}**", f"Time: {ts}"]
        for key, value in details.items():
            lines.append(f"{key}: {value}")
        lines.append("Action: Manual investigation required")
        return "\n".join(lines)
