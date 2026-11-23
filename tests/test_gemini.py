import io
import json
from unittest.mock import patch

import pytest

from app.integrations.gemini import GeminiClient
from app.services.interfaces.llm_client import EmptyLLMResponseError, LLMError


pytestmark = pytest.mark.anyio


@pytest.fixture
def client():
    return GeminiClient(api_key="test-key", model="test-model", system_prompt="Кулинария")


@pytest.fixture
def urlopen():
    with patch("app.integrations.gemini.urlopen") as mock:
        yield mock


async def test_sends_prompt_and_returns_visible_text(client, urlopen):
    parts = [{"thought": True, "text": "скрыто"}, {"text": "Ответ "}, {"text": "готов"}]
    body = {"candidates": [{"content": {"parts": parts}}]}
    urlopen.return_value = io.BytesIO(json.dumps(body).encode())
    assert await client.generate_reply("Вопрос") == "Ответ готов"
    request = urlopen.call_args.args[0]
    payload = json.loads(request.data)
    assert payload["systemInstruction"]["parts"] == [{"text": "Кулинария"}]
    assert payload["contents"] == [{"role": "user", "parts": [{"text": "Вопрос"}]}]
    assert dict(request.header_items())["X-goog-api-key"] == "test-key"
    assert "test-key" not in request.full_url


@pytest.mark.parametrize(
    "body",
    [
        {"candidates": []},
        {"promptFeedback": {"blockReason": "SAFETY"}},
        {"candidates": [{"content": {"parts": [{"text": "   "}]}}]},
    ],
    ids=["no-candidates", "blocked", "blank"],
)
async def test_empty_or_blocked_response(client, urlopen, body):
    urlopen.return_value = io.BytesIO(json.dumps(body).encode())
    with pytest.raises(EmptyLLMResponseError):
        await client.generate_reply("Вопрос")


async def test_timeout_becomes_llm_error(client, urlopen):
    urlopen.side_effect = TimeoutError()
    with pytest.raises(LLMError):
        await client.generate_reply("Вопрос")
