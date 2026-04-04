import asyncio
import os
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from src.database import Base
import src.models  # noqa: F401
from urllib.parse import urlparse, urlunparse


def _get_test_database_url():
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise OSError("DATABASE_URL environment variable is required for tests")
    parsed_url = urlparse(database_url)
    modified_path = (
        "/jobpulse_test"
        if not parsed_url.path
        else (parsed_url.path.rsplit("/", 1)[0] + "/jobpulse_test")
    )
    return urlunparse(
        (
            parsed_url.scheme,
            parsed_url.netloc,
            modified_path,
            parsed_url.params,
            parsed_url.query,
            parsed_url.fragment,
        )
    )


@pytest.fixture(scope="session")
def event_loop():
    policy = asyncio.get_event_loop_policy()
    loop = policy.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def async_engine():
    test_db_url = _get_test_database_url()
    engine = create_async_engine(
        test_db_url,
        echo=False,
        pool_size=5,
        max_overflow=10,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def async_session(async_engine):
    async_session_maker = async_sessionmaker(
        async_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with async_session_maker() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def db_session(async_session: AsyncSession):
    return async_session
