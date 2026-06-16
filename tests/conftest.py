import os

import pytest_asyncio
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from contentauto.models.content import Base

TEST_DB = os.getenv("TEST_DATABASE_URL")


@pytest_asyncio.fixture
async def _fresh_engine():
    if not TEST_DB:
        import pytest

        pytest.skip("TEST_DATABASE_URL not set")
    engine = create_async_engine(TEST_DB)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture
async def db_session(_fresh_engine):
    maker = async_sessionmaker(_fresh_engine, expire_on_commit=False)
    async with maker() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def session_maker(_fresh_engine):
    """A real async_sessionmaker on the test DB — for code that opens its own
    session (e.g. run_item_job)."""
    return async_sessionmaker(_fresh_engine, expire_on_commit=False)
