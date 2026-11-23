from datetime import UTC, datetime
from uuid import uuid4

import pytest

from app.domain.message import Message, MessageRole


def test_role_string_matches_external_representation():
    assert str(MessageRole.USER) == "user"
    assert str(MessageRole.ASSISTANT) == "assistant"


@pytest.mark.parametrize("length", [1, 500])
def test_accepts_user_message_within_length_limit(length):
    text = "a" * length
    assert Message(MessageRole.USER, text).text == text


def test_rejects_user_message_above_length_limit():
    with pytest.raises(ValueError):
        Message(MessageRole.USER, "a" * 501)


@pytest.mark.parametrize("role", list(MessageRole))
@pytest.mark.parametrize("text", ["", " ", "\t\n"], ids=["empty", "space", "tab-newline"])
def test_rejects_blank_message(role, text):
    with pytest.raises(ValueError):
        Message(role, text)


def test_assistant_response_can_exceed_user_limit():
    text = "a" * 501
    assert Message(MessageRole.ASSISTANT, text).text == text


def test_message_can_be_restored_without_changing_stored_values():
    message_id = uuid4()
    created_at = datetime(2026, 1, 1, tzinfo=UTC)
    message = Message(MessageRole.USER, " hello ", message_id, created_at)
    assert message.id == message_id
    assert message.created_at == created_at
    assert message.text == " hello "


def test_new_messages_have_distinct_ids_and_utc_timestamps():
    first = Message(MessageRole.USER, "Hello")
    second = Message(MessageRole.USER, "Hello")
    assert first.id != second.id
    assert first.created_at.tzinfo is UTC
