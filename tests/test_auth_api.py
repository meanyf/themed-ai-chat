from unittest.mock import AsyncMock

import pytest

from app.main import app
from app.services.auth import AuthService


@pytest.mark.anyio
async def test_cookie_grants_access_until_logout(http_client, session_repo):
    app.state.auth = AuthService(session_repo, "valid_key")
    app.state.chat = AsyncMock()
    app.state.chat.get_history.return_value = []
    assert (await http_client.get("/api/messages")).status_code == 401
    assert (await http_client.post("/api/messages", json={"text": "Hi"})).status_code == 401
    assert (await http_client.post("/api/auth/login", json={"key": "wrong"})).status_code == 401
    response = await http_client.post("/api/auth/login", json={"key": "valid_key"})
    assert response.status_code == 204
    assert "HttpOnly" in response.headers["set-cookie"]
    assert "Secure" in response.headers["set-cookie"]
    token = http_client.cookies["session"]
    assert (await http_client.get("/api/messages")).json() == []
    assert (await http_client.post("/api/auth/logout")).status_code == 204
    assert "session" not in http_client.cookies
    http_client.cookies.set("session", token)
    assert (await http_client.get("/api/messages")).status_code == 401
