from typing import Protocol


class LLMError(Exception):
    """Ошибка запроса к языковой модели."""


class EmptyLLMResponseError(LLMError):
    """Модель не вернула текст ответа."""


class LLMClient(Protocol):
    """Клиент тематической языковой модели."""

    async def generate_reply(self, user_text: str) -> str:
        """Возвращает текст ответа на сообщение пользователя.

        Raises:
            LLMError: Если запрос к модели завершился ошибкой.
            EmptyLLMResponseError: Если текст отсутствует, пуст или состоит
                только из пробельных символов.
        """
        ...
