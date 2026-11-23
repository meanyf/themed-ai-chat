import os
from unittest.mock import AsyncMock, patch

import pytest

from app.main import app
from app.services.interfaces.llm_client import LLMError


@pytest.mark.integration
@pytest.mark.anyio
async def test_chat_survives_lifespan_restart(http_client):
    async with app.router.lifespan_context(app):
        assert (await http_client.get("/api/messages")).status_code == 401
        login = await http_client.post("/api/auth/login", json={"key": os.environ["ACCESS_KEY"]})
        assert login.status_code == 204
        token = http_client.cookies["session"]
        assert (await http_client.get("/api/messages")).json() == []
        with patch("app.main.GeminiClient.generate_reply", new_callable=AsyncMock) as generate:
            generate.return_value = "а" * 501
            reply = await http_client.post("/api/messages", json={"text": "Вопрос"})
            assert reply.status_code == 200
            generate.side_effect = LLMError("Сбой модели")
            failed = await http_client.post("/api/messages", json={"text": "Второй вопрос"})
            assert failed.status_code == 502

    async with app.router.lifespan_context(app):
        history = await http_client.get("/api/messages")
        assert history.status_code == 200
        rows = history.json()
        assert [(row["role"], row["text"]) for row in rows] == [
            ("user", "Вопрос"),
            ("assistant", "а" * 501),
            ("user", "Второй вопрос"),
        ]
        assert rows[1] == reply.json()
        assert (await http_client.post("/api/auth/logout")).status_code == 204
        http_client.cookies.set("session", token)
        assert (await http_client.get("/api/messages")).status_code == 401
