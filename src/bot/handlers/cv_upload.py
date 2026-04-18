import logging
import uuid

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, Document
from aiogram.fsm.context import FSMContext

from src.bot.keyboards import (
    main_menu_keyboard,
    confirm_replace_keyboard,
)
from src.bot.states import CVUploadState
from src.bot.utils.i18n import t, get_locale

logger = logging.getLogger(__name__)

router = Router()


@router.message(Command("upload_cv"))
async def cmd_upload_cv(message: Message, state: FSMContext):
    locale = get_locale(message.from_user.language_code)

    from src.database import get_async_session
    from src.repositories.user_repository import UserRepository

    async for session in get_async_session():
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(message.from_user.id)
        if not user:
            await message.answer(t("not_registered", locale))
            return

    await state.set_state(CVUploadState.waiting_for_file)
    await message.answer(t("upload_prompt", locale))


@router.message(CVUploadState.waiting_for_file, F.document)
async def handle_cv_file(message: Message, state: FSMContext):
    locale = get_locale(message.from_user.language_code)
    document: Document = message.document

    file_name = document.file_name or "unknown"
    file_size = document.file_size or 0
    ext = file_name.rsplit(".", 1)[-1].lower() if "." in file_name else ""

    if ext not in ("pdf", "docx", "txt"):
        await message.answer(t("upload_error_format", locale))
        return

    if file_size > 5 * 1024 * 1024:
        await message.answer(t("upload_error_size", locale))
        return

    from src.database import get_async_session
    from src.repositories.user_repository import UserRepository
    from src.repositories.cv_repository import CVRepository
    from src.services.cv_service import SUBSCRIPTION_CV_LIMITS

    async for session in get_async_session():
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(message.from_user.id)
        if not user:
            await message.answer(t("not_registered", locale))
            await state.clear()
            return

        cv_repo = CVRepository(session)
        active_count = await cv_repo.count_active_by_user(user.id)
        tier = user.subscription_tier
        limit = SUBSCRIPTION_CV_LIMITS.get(tier, 1)

        if active_count >= limit:
            active_cv = await cv_repo.get_active_cv(user.id)
            if active_cv:
                await state.set_state(CVUploadState.confirming_replace)
                await state.update_data(
                    file_id=document.file_id,
                    file_name=file_name,
                    file_size=file_size,
                    old_cv_id=str(active_cv.id),
                )
                await message.answer(
                    t("replace_prompt", locale),
                    reply_markup=confirm_replace_keyboard(),
                )
                return
            await message.answer(t("upload_error_limit", locale))
            await state.clear()
            return

        await state.set_state(CVUploadState.processing_file)
        await _process_upload(message, state, user.id, document, session, locale)


@router.callback_query(
    CVUploadState.confirming_replace, F.data.startswith("confirm_replace:")
)
async def callback_confirm_replace(callback: CallbackQuery, state: FSMContext):
    locale = get_locale(callback.from_user.language_code)
    answer = callback.data.split(":")[1]

    if answer != "yes":
        await state.clear()
        await callback.message.edit_text(
            t("cancel", locale), reply_markup=main_menu_keyboard()
        )
        await callback.answer()
        return

    data = await state.get_data()
    file_id = data.get("file_id")
    file_name = data.get("file_name", "unknown")
    file_size = data.get("file_size", 0)
    old_cv_id = data.get("old_cv_id")

    from src.database import get_async_session
    from src.repositories.user_repository import UserRepository

    async for session in get_async_session():
        user_repo = UserRepository(session)
        user = await user_repo.get_by_telegram_id(callback.from_user.id)
        if not user:
            await callback.answer(t("not_registered", locale), show_alert=True)
            await state.clear()
            return

        await state.set_state(CVUploadState.processing_file)
        await callback.message.edit_text(t("upload_processing", locale))

        try:
            bot = callback.bot
            file = await bot.get_file(file_id)
            from io import BytesIO

            buffer = BytesIO()
            await bot.download_file(file.file_path, buffer)
            buffer.seek(0)

            from src.services.cv_service import CVService

            cv_service = CVService(session)

            if old_cv_id:
                await cv_service.replace_cv(
                    user_id=user.id,
                    old_cv_id=uuid.UUID(old_cv_id),
                    file_data=buffer,
                    filename=file_name,
                    file_size=file_size,
                )
            else:
                cv_id, _title, _text = await cv_service.upload_cv(
                    user_id=user.id,
                    file_data=buffer,
                    filename=file_name,
                    file_size=file_size,
                )

            await session.commit()

            result = await cv_service.evaluate_cv(
                uuid.UUID(old_cv_id) if old_cv_id else cv_id
            )
            await session.commit()

            score = int(float(str(result.completeness_score)))
            summary = result.experience_summary or ""
            await callback.message.edit_text(
                t("upload_success", locale, score=score, summary=summary),
                reply_markup=main_menu_keyboard(),
            )
        except Exception:
            logger.exception("CV upload failed")
            await callback.message.edit_text(
                t("error_generic", locale),
                reply_markup=main_menu_keyboard(),
            )
        finally:
            await state.clear()

    await callback.answer()


async def _process_upload(
    message: Message,
    state: FSMContext,
    user_id: uuid.UUID,
    document: Document,
    session,
    locale: str,
) -> None:
    await message.answer(t("upload_processing", locale))

    try:
        bot = message.bot
        file = await bot.get_file(document.file_id)
        from io import BytesIO

        buffer = BytesIO()
        await bot.download_file(file.file_path, buffer)
        buffer.seek(0)

        from src.services.cv_service import CVService

        cv_service = CVService(session)
        cv_id, _title, _text = await cv_service.upload_cv(
            user_id=user_id,
            file_data=buffer,
            filename=document.file_name or "unknown",
            file_size=document.file_size or 0,
        )
        await session.commit()

        result = await cv_service.evaluate_cv(cv_id)
        await session.commit()

        score = int(float(str(result.completeness_score)))
        summary = result.experience_summary or ""
        await message.answer(
            t("upload_success", locale, score=score, summary=summary),
            reply_markup=main_menu_keyboard(),
        )
    except Exception:
        logger.exception("CV upload failed")
        await message.answer(
            t("error_generic", locale), reply_markup=main_menu_keyboard()
        )
    finally:
        await state.clear()


@router.message(CVUploadState.waiting_for_file)
async def handle_invalid_file(message: Message, _state: FSMContext):
    locale = get_locale(message.from_user.language_code)
    await message.answer(t("upload_error_format", locale))
