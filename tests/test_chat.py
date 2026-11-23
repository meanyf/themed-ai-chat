import io
from unittest.mock import create_autospec, patch
from urllib.error import HTTPError

import pytest

from app.domain.message import Message, MessageRole
from app.integrations.gemini import GeminiClient
from app.main import app
from app.services.auth import AuthService
from app.services.chat import ChatService
from app.services.interfaces.llm_client import EmptyLLMResponseError, LLMClient


class InMemoryRepository:
    def __init__(self):
        self.messages: list[Message] = []

    async def save(self, message: Message) -> None:
        self.messages.append(message)

    async def get_history(self) -> list[Message]:
        return self.messages.copy()


pytestmark = pytest.mark.anyio


@pytest.fixture
def llm():
    return create_autospec(LLMClient, instance=True)


@pytest.fixture
def chat(llm):
    return ChatService(InMemoryRepository(), llm)


async def test_exchange_appears_in_history(chat, llm):
    llm.generate_reply.return_value = "Привет!"
    reply = await chat.send_message(" Привет ")
    llm.generate_reply.assert_awaited_once_with(" Привет ")
    user, assistant = await chat.get_history()
    assert (user.role, user.text) == (MessageRole.USER, " Привет ")
    assert (assistant.role, assistant.text) == (MessageRole.ASSISTANT, "Привет!")
    assert reply == assistant


async def test_empty_model_response_leaves_only_user_message(chat, llm):
    llm.generate_reply.side_effect = EmptyLLMResponseError()
    with pytest.raises(EmptyLLMResponseError):
        await chat.send_message("Вопрос")
    (user,) = await chat.get_history()
    assert (user.role, user.text) == (MessageRole.USER, "Вопрос")


async def test_invalid_input_does_not_reach_model_or_history(chat, llm):
    with pytest.raises(ValueError):
        await chat.send_message("   ")
    llm.generate_reply.assert_not_awaited()
    assert await chat.get_history() == []


@pytest.mark.parametrize(
    ("body", "detail"),
    [
        (
            b'{"error": {"message": "This model is currently experiencing high demand."}}',
            "This model is currently experiencing high demand.",
        ),
        (b"Service unavailable", "Не удалось получить ответ модели."),
        (
            b'{"error": {"message": "Invalid API key: secret-gemini-key"}}',
            "Invalid API key: [скрыто]",
        ),
    ],
    ids=["provider-message", "no-json", "redacted-key"],
)
async def test_chat_api_shows_provider_error(http_client, session_repo, body, detail):
    app.state.auth = AuthService(session_repo, "valid_key")
    llm = GeminiClient(api_key="secret-gemini-key", model="test-model", system_prompt="Кулинария")
    app.state.chat = ChatService(InMemoryRepository(), llm)
    login = await http_client.post("/api/auth/login", json={"key": "valid_key"})
    assert login.status_code == 204

    error = HTTPError("https://example.com", 503, "Unavailable", {}, io.BytesIO(body))
    with patch("app.integrations.gemini.urlopen", side_effect=error):
        response = await http_client.post("/api/messages", json={"text": "Вопрос"})

    assert response.status_code == 502
    assert response.json() == {"detail": detail}
