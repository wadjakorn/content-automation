from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine

from contentauto.config import get_settings

_engine: AsyncEngine | None = None


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = create_async_engine(get_settings().database_url, pool_pre_ping=True)
    return _engine


def session_factory() -> async_sessionmaker:  # type: ignore[type-arg]
    return async_sessionmaker(get_engine(), expire_on_commit=False)
