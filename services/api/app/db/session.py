from collections.abc import AsyncGenerator
from typing import Any

from sqlalchemy import Engine, create_engine
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

_async_engine: AsyncEngine | None = None
_AsyncSessionLocal: async_sessionmaker[AsyncSession] | None = None
_sync_engine: Engine | None = None


def get_async_engine() -> AsyncEngine:
    global _async_engine
    if _async_engine is None:
        try:
            _async_engine = create_async_engine(
                settings.DATABASE_URL,
                echo=False,
                future=True,
            )
        except Exception:
            _async_engine = create_async_engine(
                "sqlite+aiosqlite:///:memory:",
                echo=False,
                future=True,
            )
    return _async_engine


def get_async_session_local() -> async_sessionmaker[AsyncSession]:
    global _AsyncSessionLocal
    if _AsyncSessionLocal is None:
        _AsyncSessionLocal = async_sessionmaker(
            bind=get_async_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return _AsyncSessionLocal


def get_sync_engine() -> Engine:
    global _sync_engine
    if _sync_engine is None:
        try:
            _sync_engine = create_engine(
                settings.DATABASE_URL_SYNC,
                echo=False,
                future=True,
            )
        except Exception:
            _sync_engine = create_engine(
                "sqlite:///:memory:",
                echo=False,
                future=True,
            )
    return _sync_engine


def __getattr__(name: str) -> Any:
    if name == "async_engine":
        return get_async_engine()
    elif name == "AsyncSessionLocal":
        return get_async_session_local()
    elif name == "sync_engine":
        return get_sync_engine()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    session_factory = get_async_session_local()
    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.close()
