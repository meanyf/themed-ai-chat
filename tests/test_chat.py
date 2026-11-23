from unittest.mock import create_autospec

import pytest

from app.domain.message import Message, MessageRole
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
