from app.domain.message import Message, MessageRole
from app.services.interfaces.llm_client import LLMClient
from app.services.interfaces.message_repository import MessageRepository


class ChatService:
    """Отправка сообщений и чтение истории тематического чата."""

    def __init__(self, repository: MessageRepository, llm: LLMClient) -> None:
        self._repository = repository
        self._llm = llm

    async def send_message(self, text: str) -> Message:
        """Сохраняет сообщение пользователя и возвращает сохранённый ответ модели.

        При ошибке модели сообщение пользователя остаётся в истории.
        """
        user = Message(role=MessageRole.USER, text=text)
        await self._repository.save(user)
        reply_text = await self._llm.generate_reply(user.text)
        reply = Message(role=MessageRole.ASSISTANT, text=reply_text)
        await self._repository.save(reply)
        return reply

    async def get_history(self) -> list[Message]:
        """Возвращает историю чата в хронологическом порядке."""
        return await self._repository.get_history()
