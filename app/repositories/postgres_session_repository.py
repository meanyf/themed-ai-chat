from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.schema import sessions
from app.domain.session import Session


class PostgresSessionRepository:
    """Хранит сессии доступа к чату в PostgreSQL."""

    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self._sessions = sessions

    async def create(self, session: Session) -> None:
        async with self._sessions.begin() as db:
            await db.execute(sessions.insert().values(
                token_hash=session.token_hash, expires_at=session.expires_at,
            ))

    async def find_by_hash(self, token_hash: str) -> Session | None:
        async with self._sessions() as db:
            result = await db.execute(select(sessions).where(sessions.c.token_hash == token_hash))
            row = result.one_or_none()
            if row is None:
                return None
            return Session(token_hash=row.token_hash, expires_at=row.expires_at)

    async def delete(self, token_hash: str) -> None:
        async with self._sessions.begin() as db:
            await db.execute(sessions.delete().where(sessions.c.token_hash == token_hash))
