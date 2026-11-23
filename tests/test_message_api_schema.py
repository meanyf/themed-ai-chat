from app.main import app


def test_public_message_schema_for_history_and_reply():
    spec = app.openapi()
    operations = spec["paths"]["/api/messages"]
    for method in ("get", "post"):
        schema = operations[method]["responses"]["200"]["content"]["application/json"]["schema"]
        item = schema["items"] if method == "get" else schema
        assert item["$ref"] == "#/components/schemas/MessageResponse"
    fields = spec["components"]["schemas"]["MessageResponse"]["properties"]
    assert set(fields) == {"id", "role", "text", "created_at"}
