import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, ErrorEvent
from aiogram.fsm.context import FSMContext

from src.bot.keyboards import main_menu_keyboard
from src.bot.utils.i18n import t, get_locale

logger = logging.getLogger(__name__)

router = Router()


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    locale = get_locale(message.from_user.language_code)
    current_state = await state.get_state()

    if current_state is None:
        await message.answer(
            t("cancel", locale),
            reply_markup=main_menu_keyboard(),
        )
        return

    await state.clear()

    from src.services.bot_session_service import BotSessionService

    svc = BotSessionService()
    await svc.clear_session(message.from_user.id)

    await message.answer(
        t("cancel", locale),
        reply_markup=main_menu_keyboard(),
    )


@router.error()
async def on_error(event: ErrorEvent, state: FSMContext):
    logger.exception("Unhandled error in bot: %s", event.exception)

    update = event.update
    lang_code = None
    if hasattr(update, "message") and update.message and update.message.from_user:
        lang_code = update.message.from_user.language_code
    elif (
        hasattr(update, "callback_query")
        and update.callback_query
        and update.callback_query.from_user
    ):
        lang_code = update.callback_query.from_user.language_code
    locale = get_locale(lang_code)

    try:
        await state.clear()
    except Exception:
        pass

    try:
        if hasattr(update, "message") and update.message:
            await update.message.answer(
                t("error_generic", locale),
                reply_markup=main_menu_keyboard(),
            )
        elif hasattr(update, "callback_query") and update.callback_query:
            await update.callback_query.answer(
                t("error_generic", locale),
                show_alert=True,
            )
    except Exception:
        logger.exception("Failed to send error message")
