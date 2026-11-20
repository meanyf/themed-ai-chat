"""Адаптер REST API Gemini для тематического чата."""

import asyncio
import json
from http.client import HTTPException
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen

from app.services.interfaces.llm_client import EmptyLLMResponseError, LLMError


class GeminiClient:
    """Генерирует текстовые ответы с заданной системной инструкцией."""

    def __init__(self, *, api_key: str, model: str, system_prompt: str) -> None:
        self._api_key = api_key
        self._url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{quote(model, safe='')}:generateContent"
        )
        self._system_prompt = system_prompt

    async def generate_reply(self, user_text: str) -> str:
        """Возвращает ответ модели на сообщение пользователя."""
        return await asyncio.to_thread(self._generate_reply, user_text)

    def _generate_reply(self, user_text: str) -> str:
        payload = {
            "systemInstruction": {"parts": [{"text": self._system_prompt}]},
            "contents": [{"role": "user", "parts": [{"text": user_text}]}],
        }
        request = Request(
            self._url,
            data=json.dumps(payload).encode(),
            headers={"Content-Type": "application/json", "x-goog-api-key": self._api_key},
        )
        try:
            with urlopen(request, timeout=30) as response:
                body = json.load(response)
        except HTTPError as exc:
            exc.close()
            raise LLMError(f"Gemini вернул ошибку HTTP {exc.code}.") from exc
        except (OSError, HTTPException) as exc:
            raise LLMError("Не удалось получить ответ от Gemini.") from exc
        except ValueError as exc:
            raise LLMError("Gemini вернул некорректный JSON.") from exc

        return _extract_reply(body)


def _extract_reply(body: dict) -> str:
    """Извлекает видимый текст из декодированного ответа Gemini."""
    try:
        candidates = body.get("candidates") or []
        candidate = candidates[0] if candidates else {}
        if body.get("promptFeedback", {}).get("blockReason") or candidate.get(
            "finishReason"
        ) in {"SAFETY", "BLOCKLIST", "PROHIBITED_CONTENT", "SPII", "RECITATION"}:
            raise EmptyLLMResponseError("Gemini заблокировал ответ.")
        parts = candidate.get("content", {}).get("parts", [])
        text = "".join(part.get("text", "") for part in parts if not part.get("thought"))
    except (AttributeError, KeyError, TypeError) as exc:
        raise LLMError("Gemini вернул ответ неожиданного формата.") from exc
    if not text.strip():
        raise EmptyLLMResponseError("Модель вернула пустой ответ.")
    return text
