from unittest import TestCase

from app.main import app


class MessageSchemaTests(TestCase):
    def test_public_message_schema_for_history_and_reply(self):
        spec = app.openapi()
        operations = spec["paths"]["/api/messages"]
        for method in ("get", "post"):
            schema = operations[method]["responses"]["200"]["content"]["application/json"]["schema"]
            item = schema["items"] if method == "get" else schema
            self.assertEqual(item["$ref"], "#/components/schemas/MessageResponse")
        fields = spec["components"]["schemas"]["MessageResponse"]["properties"]
        self.assertEqual(set(fields), {"id", "role", "text", "created_at"})
