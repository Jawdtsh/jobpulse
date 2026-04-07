from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.services.admin_alert_service import AdminAlertService


@pytest.fixture
def mock_settings():
    with patch("src.services.admin_alert_service.get_settings") as m:
        s = MagicMock()
        s.telegram.admin_alert_channel_id = "-1001234567890"
        s.telegram.telethon_api_id = 12345
        s.telegram.telethon_api_hash = "abcdef1234567890abcdef1234567890"
        s.telegram.bot_token = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
        m.return_value = s
        yield s


@pytest.fixture
def service():
    return AdminAlertService()


class TestSendAlertSkipped:
    @pytest.mark.asyncio
    async def test_skips_when_channel_id_not_configured(self, service):
        with patch("src.services.admin_alert_service.get_settings") as m:
            s = MagicMock()
            s.telegram.admin_alert_channel_id = None
            m.return_value = s
            await service.send_alert("test_error", {"key": "value"})


class TestSendAlertSuccess:
    @pytest.mark.asyncio
    async def test_sends_alert_via_bot_token_auth(self, service, mock_settings):
        with patch(
            "src.services.admin_alert_service.TelegramClient"
        ) as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value = mock_client

            await service.send_alert("sessions_exhausted", {"channel": "test_ch"})

            mock_client_cls.assert_called_once_with(
                "admin_alert_session",
                12345,
                "abcdef1234567890abcdef1234567890",
            )
            mock_client.connect.assert_awaited_once()
            mock_client.sign_in.assert_awaited_once_with(
                bot_token="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"
            )
            mock_client.send_message.assert_awaited_once()
            mock_client.disconnect.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_sends_to_configured_channel_id(self, service, mock_settings):
        with patch(
            "src.services.admin_alert_service.TelegramClient"
        ) as mock_client_cls:
            mock_client = AsyncMock()
            mock_client_cls.return_value = mock_client

            await service.send_alert("ai_failure", {"provider": "gemini"})

            call_args = mock_client.send_message.call_args
            assert call_args[0][0] == -1001234567890


class TestSendAlertError:
    @pytest.mark.asyncio
    async def test_logs_exception_on_send_failure(self, service, mock_settings):
        with (
            patch("src.services.admin_alert_service.TelegramClient") as mock_client_cls,
            patch("src.services.admin_alert_service.logger") as mock_logger,
        ):
            mock_client = AsyncMock()
            mock_client.connect.side_effect = ConnectionError("network error")
            mock_client_cls.return_value = mock_client

            await service.send_alert("crash", {"error": "test"})

            mock_logger.exception.assert_called_once()


class TestFormatMessage:
    def test_includes_error_type_and_timestamp(self, service):
        msg = service._format_message("sessions_banned", {"count": "3"})

        assert "**JobPulse Alert**" in msg
        assert "`sessions_banned`" in msg
        assert "Time:" in msg
        assert "`3`" in msg

    def test_handles_empty_details(self, service):
        msg = service._format_message("pipeline_crash", {})

        assert "**JobPulse Alert**" in msg
        assert "`pipeline_crash`" in msg
        assert "Time:" in msg
