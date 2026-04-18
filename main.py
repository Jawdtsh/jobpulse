import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config.settings import get_settings
from src.bot.router import main_router
from src.bot.middlewares import AuthMiddleware, RateLimiterMiddleware
from src.bot.utils.logger import setup_logging

logger = logging.getLogger(__name__)


async def main() -> None:
    setup_logging()
    settings = get_settings()

    bot = Bot(token=settings.telegram.bot_token, parse_mode=ParseMode.HTML)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    dp.message.middleware(AuthMiddleware())
    dp.message.middleware(RateLimiterMiddleware())
    dp.callback_query.middleware(AuthMiddleware())
    dp.callback_query.middleware(RateLimiterMiddleware())

    dp.include_router(main_router)

    from src.bot.health import start_health_server

    health_task = asyncio.create_task(start_health_server())

    logger.info("Starting bot polling...")
    try:
        await dp.start_polling(bot)
    finally:
        health_task.cancel()


if __name__ == "__main__":
    asyncio.run(main())
