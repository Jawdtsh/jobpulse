import logging

logger = logging.getLogger(__name__)

_bot_instance = None


def _get_bot():
    global _bot_instance
    if _bot_instance is None:
        from aiogram import Bot
        from config.settings import get_settings

        settings = get_settings()
        _bot_instance = Bot(token=settings.telegram.bot_token)
    return _bot_instance


async def send_telegram_message(
    chat_id: int,
    text: str,
    job_id: str | None = None,
    cv_id: str | None = None,
) -> None:
    bot = _get_bot()
    reply_markup = None

    if job_id:
        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

        buttons = []
        callback_data_view = f"view:{job_id}"
        buttons.append(
            InlineKeyboardButton(text="View Details", callback_data=callback_data_view)
        )
        if cv_id:
            callback_data_cover = f"cover:{job_id}:{cv_id}"
            buttons.append(
                InlineKeyboardButton(
                    text="Generate Cover Letter", callback_data=callback_data_cover
                )
            )
        reply_markup = InlineKeyboardMarkup(inline_keyboard=[buttons])

    try:
        await bot.send_message(
            chat_id=chat_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode="HTML",
        )
    except Exception as e:
        logger.error("Failed to send Telegram message to %s: %s", chat_id, e)
        raise
