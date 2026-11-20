from typing import Protocol


class EmptyLLMResponseError(Exception):
    """Модель не вернула текст ответа."""


class LLMClient(Protocol):
    """Клиент тематической языковой модели."""

    async def generate_reply(self, user_text: str) -> str:
        """Возвращает текст ответа на сообщение пользователя.

        Raises:
            EmptyLLMResponseError: Если текст отсутствует, пуст или состоит
                только из пробельных символов.
        """
        ...
