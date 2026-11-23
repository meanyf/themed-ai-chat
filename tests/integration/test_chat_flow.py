import os
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.services.interfaces.llm_client import LLMError


@pytest.mark.integration
class ChatFlowIntegrationTests(IsolatedAsyncioTestCase):
    async def test_chat_survives_lifespan_restart(self):
        client = AsyncClient(transport=ASGITransport(app=app), base_url="http://test")
        self.addAsyncCleanup(client.aclose)
        async with app.router.lifespan_context(app):
            self.assertEqual((await client.get("/api/messages")).status_code, 401)
            login = await client.post("/api/auth/login", json={"key": os.environ["ACCESS_KEY"]})
            self.assertEqual(login.status_code, 204)
            token = client.cookies["session"]
            self.assertEqual((await client.get("/api/messages")).json(), [])
            with patch("app.main.GeminiClient.generate_reply", new_callable=AsyncMock) as generate:
                generate.return_value = "а" * 501
                reply = await client.post("/api/messages", json={"text": "Вопрос"})
                self.assertEqual(reply.status_code, 200)
                generate.side_effect = LLMError("Сбой модели")
                failed = await client.post("/api/messages", json={"text": "Второй вопрос"})
                self.assertEqual(failed.status_code, 502)

        async with app.router.lifespan_context(app):
            history = await client.get("/api/messages")
            self.assertEqual(history.status_code, 200)
            rows = history.json()
            self.assertEqual([(row["role"], row["text"]) for row in rows], [
                ("user", "Вопрос"), ("assistant", "а" * 501), ("user", "Второй вопрос"),
            ])
            self.assertEqual(rows[1], reply.json())
            self.assertEqual((await client.post("/api/auth/logout")).status_code, 204)
            client.cookies.set("session", token)
            self.assertEqual((await client.get("/api/messages")).status_code, 401)
