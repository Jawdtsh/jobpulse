import asyncio
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from src.database import Base
from config.settings import get_settings
from urllib.parse import urlparse, urlunparse

settings = get_settings()

# Parse the database URL and safely replace the database name
parsed_url = urlparse(settings.database_url)
# Replace the path/dbname with jobpulse_test
modified_path = (
    parsed_url.path.rsplit("/", 1)[0] + "/jobpulse_test"
    if "/" in parsed_url.path
    else "/jobpulse_test"
)
# Reconstruct the URL
TEST_DATABASE_URL = urlunparse(
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
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def async_engine():
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
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
