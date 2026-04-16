import logging

from aiohttp import web

logger = logging.getLogger(__name__)

_app: web.Application | None = None


async def _health_handler(request: web.Request) -> web.Response:
    checks = {"bot": "ok"}

    try:
        from config.settings import get_settings
        import redis.asyncio as aioredis

        settings = get_settings()
        r = aioredis.from_url(settings.redis.redis_url)
        await r.ping()
        await r.aclose()
        checks["redis"] = "ok"
    except Exception as e:
        checks["redis"] = f"error: {e}"

    try:
        from src.database import get_async_session

        async for session in get_async_session():
            await session.execute(__import__("sqlalchemy").text("SELECT 1"))
            break
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {e}"

    status_code = 200 if all(v == "ok" for v in checks.values()) else 503
    return web.json_response(checks, status=status_code)


def create_health_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/health", _health_handler)
    return app


async def start_health_server(port: int = 8080) -> None:
    global _app
    _app = create_health_app()
    runner = web.AppRunner(_app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info("Health endpoint started on port %d", port)
