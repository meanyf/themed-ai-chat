from datetime import UTC, datetime, timedelta
from hashlib import sha256
from unittest import IsolatedAsyncioTestCase

from app.domain.session import Session
from app.services.auth import AuthService, AuthenticationError


class MemorySessions:
    def __init__(self):
        self.sessions = {}

    async def create(self, session):
        self.sessions[session.token_hash] = session

    async def find_by_hash(self, token_hash):
        return self.sessions.get(token_hash)

    async def delete(self, token_hash):
        self.sessions.pop(token_hash, None)


class AuthTests(IsolatedAsyncioTestCase):
    def setUp(self):
        self.repo = MemorySessions()
        self.auth = AuthService(self.repo, "valid_key")

    async def test_invalid_login_creates_no_session(self):
        for key in ("wrong_key", "неверный"):
            with self.assertRaises(AuthenticationError):
                await self.auth.login(key)
        self.assertFalse(self.repo.sessions)

    async def test_logout_revokes_only_one_session(self):
        first = await self.auth.login("valid_key")
        second = await self.auth.login("valid_key")
        session = await self.auth.authenticate(first)
        self.assertEqual(session.token_hash, sha256(first.encode()).hexdigest())
        await self.auth.logout(first)
        with self.assertRaises(AuthenticationError):
            await self.auth.authenticate(first)
        await self.auth.authenticate(second)

    async def test_expiration_boundary(self):
        end = datetime.now(UTC)
        session = Session(sha256(b"token").hexdigest(), end)
        self.assertFalse(session.is_expired(end - timedelta(microseconds=1)))
        self.assertTrue(session.is_expired(end))
        await self.repo.create(session)
        with self.assertRaises(AuthenticationError):
            await self.auth.authenticate("token")
