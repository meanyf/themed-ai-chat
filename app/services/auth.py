import secrets
from datetime import UTC, datetime, timedelta
from hashlib import sha256

from app.domain.session import Session
from app.services.interfaces.session_repository import SessionRepository


class AuthenticationError(Exception):
    """Ключ доступа или сессия недействительны."""


def _token_hash(token: str) -> str:
    return sha256(token.encode()).hexdigest()


class AuthService:
    """Управляет входом по общему ключу и сессиями чата."""

    def __init__(
        self, repository: SessionRepository, access_key: str,
        session_ttl: timedelta = timedelta(hours=24),
    ) -> None:
        self._repository = repository
        self._access_key = access_key.encode()
        self._session_ttl = session_ttl

    async def login(self, key: str) -> str:
        if not secrets.compare_digest(key.encode(), self._access_key):
            raise AuthenticationError("Неверный ключ доступа.")
        token = secrets.token_urlsafe(32)
        session = Session(_token_hash(token), datetime.now(UTC) + self._session_ttl)
        await self._repository.create(session)
        return token

    async def authenticate(self, token: str) -> Session:
        session = await self._repository.find_by_hash(_token_hash(token))
        if session is None or session.is_expired(datetime.now(UTC)):
            raise AuthenticationError("Сессия недействительна.")
        return session

    async def logout(self, token: str) -> None:
        await self._repository.delete(_token_hash(token))
