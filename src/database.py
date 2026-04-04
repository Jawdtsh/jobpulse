from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


_engine = None
_async_session_maker = None


def _ensure_engine():
    global _engine, _async_session_maker
    if _engine is not None:
        return
    from config.settings import get_settings

    s = get_settings()
    _engine = create_async_engine(
        s.database.database_url,
        pool_size=s.database.pool_size,
        max_overflow=s.database.max_overflow,
    )
    _async_session_maker = async_sessionmaker(
        _engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    _ensure_engine()
    async with _async_session_maker() as session:
        yield session


def __getattr__(name):
    if name == "engine":
        _ensure_engine()
        return _engine
    if name == "async_session_maker":
        _ensure_engine()
        return _async_session_maker
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
