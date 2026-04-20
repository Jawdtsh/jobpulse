import logging

from aiogram import Router

from src.bot.handlers.registration import router as registration_router
from src.bot.handlers.cv_upload import router as cv_upload_router
from src.bot.handlers.cv_management import router as cv_management_router
from src.bot.handlers.job_notifications import router as job_notifications_router
from src.bot.handlers.saved_jobs import router as saved_jobs_router
from src.bot.handlers.settings import router as settings_router
from src.bot.handlers.referral import router as referral_router
from src.bot.handlers.subscription import router as subscription_router
from src.bot.handlers.errors import router as errors_router
from src.bot.handlers.cover_letter import router as cover_letter_router

logger = logging.getLogger(__name__)

main_router = Router()

main_router.include_router(registration_router)
main_router.include_router(cv_upload_router)
main_router.include_router(cv_management_router)
main_router.include_router(job_notifications_router)
main_router.include_router(saved_jobs_router)
main_router.include_router(settings_router)
main_router.include_router(referral_router)
main_router.include_router(subscription_router)
main_router.include_router(errors_router)
main_router.include_router(cover_letter_router)

logger.info("All bot handlers registered")
