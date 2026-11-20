import unittest
from datetime import UTC, datetime
from uuid import uuid4

from app.domain.message import Message, MessageRole


class MessageTests(unittest.TestCase):
    def test_role_string_matches_external_representation(self):
        self.assertEqual(str(MessageRole.USER), "user")
        self.assertEqual(str(MessageRole.ASSISTANT), "assistant")

    def test_user_message_length_boundaries(self):
        for length in (1, 500):
            with self.subTest(length=length):
                self.assertEqual(Message(MessageRole.USER, "a" * length).text, "a" * length)
        with self.assertRaises(ValueError):
            Message(MessageRole.USER, "a" * 501)

    def test_blank_messages_are_rejected_for_both_roles(self):
        for role in MessageRole:
            for text in ("", " ", "\t\n"):
                with self.subTest(role=role, text=text):
                    with self.assertRaises(ValueError):
                        Message(role, text)

    def test_assistant_response_can_exceed_user_limit(self):
        text = "a" * 501
        self.assertEqual(Message(MessageRole.ASSISTANT, text).text, text)

    def test_message_can_be_restored_without_changing_stored_values(self):
        message_id = uuid4()
        created_at = datetime(2026, 1, 1, tzinfo=UTC)
        message = Message(MessageRole.USER, " hello ", message_id, created_at)
        self.assertEqual(message.id, message_id)
        self.assertEqual(message.created_at, created_at)
        self.assertEqual(message.text, " hello ")

    def test_new_messages_have_distinct_ids_and_utc_timestamps(self):
        first = Message(MessageRole.USER, "Hello")
        second = Message(MessageRole.USER, "Hello")
        self.assertNotEqual(first.id, second.id)
        self.assertEqual(first.created_at.tzinfo, UTC)


if __name__ == "__main__":
    unittest.main()
