"""Сущности и правила чата, независимые от хранения и транспорта."""

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4


MAX_USER_MESSAGE_LENGTH = 500


class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"


@dataclass(frozen=True, slots=True)
class Message:
    role: MessageRole
    text: str
    id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    def __post_init__(self) -> None:
        if not isinstance(self.role, MessageRole):
            raise ValueError("Message role must be a MessageRole value.")
        if not isinstance(self.text, str) or not self.text.strip():
            raise ValueError("Message text must not be empty or whitespace-only.")
        if self.role == MessageRole.USER and len(self.text) > MAX_USER_MESSAGE_LENGTH:
            raise ValueError(
                f"User message must not exceed {MAX_USER_MESSAGE_LENGTH} characters."
            )
