from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.db.schema import messages
from app.domain.message import Message, MessageRole


class PostgresMessageRepository:
    """Хранит историю чата в PostgreSQL."""

    def __init__(self, sessions: async_sessionmaker[AsyncSession]) -> None:
        self._sessions = sessions

    async def save(self, message: Message) -> None:
        async with self._sessions.begin() as session:
            await session.execute(messages.insert().values(
                id=message.id, role=message.role.value, text=message.text,
                created_at=message.created_at,
            ))

    async def get_history(self) -> list[Message]:
        async with self._sessions() as session:
            rows = await session.execute(select(messages).order_by(messages.c.created_at, messages.c.id))
            return [
                Message(id=row.id, role=MessageRole(row.role), text=row.text, created_at=row.created_at)
                for row in rows
            ]
