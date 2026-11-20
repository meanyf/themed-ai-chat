from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock

from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.auth import AuthService
from test_auth import MemorySessions


class AuthApiTests(IsolatedAsyncioTestCase):
    async def test_cookie_grants_access_until_logout(self):
        app.state.auth = AuthService(MemorySessions(), "valid_key")
        app.state.chat = AsyncMock()
        app.state.chat.get_history.return_value = []
        client = AsyncClient(transport=ASGITransport(app=app), base_url="https://testserver")
        self.addAsyncCleanup(client.aclose)
        self.assertEqual((await client.get("/api/messages")).status_code, 401)
        self.assertEqual((await client.post("/api/messages", json={"text": "Hi"})).status_code, 401)
        self.assertEqual((await client.post("/api/auth/login", json={"key": "wrong"})).status_code, 401)
        response = await client.post("/api/auth/login", json={"key": "valid_key"})
        self.assertEqual(response.status_code, 204)
        self.assertIn("HttpOnly", response.headers["set-cookie"])
        self.assertIn("Secure", response.headers["set-cookie"])
        token = client.cookies["session"]
        self.assertEqual((await client.get("/api/messages")).json(), [])
        self.assertEqual((await client.post("/api/auth/logout")).status_code, 204)
        self.assertNotIn("session", client.cookies)
        client.cookies.set("session", token)
        self.assertEqual((await client.get("/api/messages")).status_code, 401)
