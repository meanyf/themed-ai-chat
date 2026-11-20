import io
import json
from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch

from app.integrations.gemini import GeminiClient
from app.services.interfaces.llm_client import EmptyLLMResponseError, LLMError


class GeminiTests(IsolatedAsyncioTestCase):
    def setUp(self):
        self.client = GeminiClient(api_key="test-key", model="test-model", system_prompt="Кулинария")
        self.open = self.enterContext(patch("app.integrations.gemini.urlopen"))

    def respond(self, body):
        self.open.return_value = io.BytesIO(json.dumps(body).encode())

    async def test_sends_prompt_and_returns_visible_text(self):
        parts = [{"thought": True, "text": "скрыто"}, {"text": "Ответ "}, {"text": "готов"}]
        self.respond({"candidates": [{"content": {"parts": parts}}]})
        self.assertEqual(await self.client.generate_reply("Вопрос"), "Ответ готов")
        request = self.open.call_args.args[0]
        payload = json.loads(request.data)
        self.assertEqual(payload["systemInstruction"]["parts"], [{"text": "Кулинария"}])
        self.assertEqual(payload["contents"], [{"role": "user", "parts": [{"text": "Вопрос"}]}])
        self.assertEqual(dict(request.header_items())["X-goog-api-key"], "test-key")
        self.assertNotIn("test-key", request.full_url)

    async def test_empty_or_blocked_response(self):
        for body in ({"candidates": []}, {"promptFeedback": {"blockReason": "SAFETY"}},
                     {"candidates": [{"content": {"parts": [{"text": "   "}]}}]}):
            with self.subTest(body=body):
                self.respond(body)
                with self.assertRaises(EmptyLLMResponseError):
                    await self.client.generate_reply("Вопрос")

    async def test_timeout_becomes_llm_error(self):
        self.open.side_effect = TimeoutError()
        with self.assertRaises(LLMError):
            await self.client.generate_reply("Вопрос")
