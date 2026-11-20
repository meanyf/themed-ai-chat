from typing import Protocol

from app.domain.message import Message


class MessageRepository(Protocol):
    """Хранилище сообщений чата."""

    async def save(self, message: Message) -> None:
        """Сохраняет сообщение с его исходными идентификатором и временем."""
        ...

    async def get_history(self) -> list[Message]:
        """Возвращает сообщения от самых ранних к самым поздним."""
        ...
