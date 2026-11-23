import pytest
from httpx import ASGITransport, AsyncClient
from starlette.datastructures import State

from app.main import app


class MemorySessions:
    def __init__(self):
        self.sessions = {}

    async def create(self, session):
        self.sessions[session.token_hash] = session

    async def find_by_hash(self, token_hash):
        return self.sessions.get(token_hash)

    async def delete(self, token_hash):
        self.sessions.pop(token_hash, None)


@pytest.fixture
def session_repo():
    return MemorySessions()


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def http_client(monkeypatch):
    monkeypatch.setattr(app, "state", State())
    async with AsyncClient(transport=ASGITransport(app=app), base_url="https://testserver") as client:
        yield client
