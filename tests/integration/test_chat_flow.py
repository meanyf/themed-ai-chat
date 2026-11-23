import os
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from alembic import command
from alembic.config import Config

from app.main import app
from app.services.interfaces.llm_client import LLMError


@pytest.fixture
def migrated_database(monkeypatch):
    """Применяет миграции к базе, явно выделенной для тестов."""
    database_url = os.environ.get("TEST_DATABASE_URL")
    if not database_url:
        pytest.fail("Задайте TEST_DATABASE_URL или запустите тесты через compose.test.yml.", pytrace=False)
    monkeypatch.setenv("DATABASE_URL", database_url)
    config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    command.upgrade(config, "head")


@pytest.mark.integration
@pytest.mark.anyio
@pytest.mark.usefixtures("migrated_database")
async def test_chat_survives_lifespan_restart(http_client):
    async with app.router.lifespan_context(app):
        assert (await http_client.get("/api/messages")).status_code == 401
        login = await http_client.post("/api/auth/login", json={"key": os.environ["ACCESS_KEY"]})
        assert login.status_code == 204
        token = http_client.cookies["session"]
        history_before = await http_client.get("/api/messages")
        assert history_before.status_code == 200
        previous_rows = history_before.json()
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
        assert rows[:len(previous_rows)] == previous_rows
        new_rows = rows[len(previous_rows):]
        assert [(row["role"], row["text"]) for row in new_rows] == [
            ("user", "Вопрос"),
            ("assistant", "а" * 501),
            ("user", "Второй вопрос"),
        ]
        assert new_rows[1] == reply.json()
        assert (await http_client.post("/api/auth/logout")).status_code == 204
        http_client.cookies.set("session", token)
        assert (await http_client.get("/api/messages")).status_code == 401
