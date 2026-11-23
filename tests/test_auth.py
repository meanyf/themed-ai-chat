from datetime import UTC, datetime, timedelta
from hashlib import sha256

import pytest

from app.domain.session import Session
from app.services.auth import AuthService, AuthenticationError


pytestmark = pytest.mark.anyio


@pytest.fixture
def auth(session_repo):
    return AuthService(session_repo, "valid_key")


@pytest.mark.parametrize("key", ["wrong_key", "неверный"], ids=["wrong-key", "non-ascii"])
async def test_invalid_login_creates_no_session(auth, session_repo, key):
    with pytest.raises(AuthenticationError):
        await auth.login(key)
    assert not session_repo.sessions


async def test_logout_revokes_only_one_session(auth):
    first = await auth.login("valid_key")
    second = await auth.login("valid_key")
    session = await auth.authenticate(first)
    assert session.token_hash == sha256(first.encode()).hexdigest()
    await auth.logout(first)
    with pytest.raises(AuthenticationError):
        await auth.authenticate(first)
    await auth.authenticate(second)


async def test_expiration_boundary(auth, session_repo):
    end = datetime.now(UTC)
    session = Session(sha256(b"token").hexdigest(), end)
    assert not session.is_expired(end - timedelta(microseconds=1))
    assert session.is_expired(end)
    await session_repo.create(session)
    with pytest.raises(AuthenticationError):
        await auth.authenticate("token")
