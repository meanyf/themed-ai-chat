from unittest import IsolatedAsyncioTestCase
from unittest.mock import create_autospec

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


class ChatServiceTests(IsolatedAsyncioTestCase):
    def setUp(self):
        self.repository = InMemoryRepository()
        self.llm = create_autospec(LLMClient, instance=True)
        self.chat = ChatService(self.repository, self.llm)

    async def test_exchange_appears_in_history(self):
        self.llm.generate_reply.return_value = "Привет!"
        reply = await self.chat.send_message(" Привет ")
        self.llm.generate_reply.assert_awaited_once_with(" Привет ")
        user, assistant = await self.chat.get_history()
        self.assertEqual((user.role, user.text), (MessageRole.USER, " Привет "))
        self.assertEqual((assistant.role, assistant.text), (MessageRole.ASSISTANT, "Привет!"))
        self.assertEqual(reply, assistant)

    async def test_empty_model_response_leaves_only_user_message(self):
        self.llm.generate_reply.side_effect = EmptyLLMResponseError()
        with self.assertRaises(EmptyLLMResponseError):
            await self.chat.send_message("Вопрос")
        (user,) = await self.chat.get_history()
        self.assertEqual((user.role, user.text), (MessageRole.USER, "Вопрос"))

    async def test_invalid_input_does_not_reach_model_or_history(self):
        with self.assertRaises(ValueError):
            await self.chat.send_message("   ")
        self.llm.generate_reply.assert_not_awaited()
        self.assertEqual(await self.chat.get_history(), [])
