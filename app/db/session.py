from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine


@asynccontextmanager
async def database_sessions(url: str) -> AsyncGenerator[async_sessionmaker[AsyncSession], None]:
    """Предоставляет фабрику сессий и закрывает пул при остановке приложения."""
    engine = create_async_engine(url, pool_pre_ping=True)
    try:
        yield async_sessionmaker(engine, expire_on_commit=False)
    finally:
        await engine.dispose()
