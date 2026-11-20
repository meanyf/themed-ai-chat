from typing import Protocol

from app.domain.session import Session


class SessionRepository(Protocol):
    """Хранилище сессий доступа к чату."""

    async def create(self, session: Session) -> None: ...

    async def find_by_hash(self, token_hash: str) -> Session | None: ...

    async def delete(self, token_hash: str) -> None: ...
