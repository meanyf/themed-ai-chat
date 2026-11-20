from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.message import MAX_USER_MESSAGE_LENGTH, MessageRole


class MessageRequest(BaseModel):
    text: str = Field(min_length=1, max_length=MAX_USER_MESSAGE_LENGTH, pattern=r"\S")


class MessageResponse(BaseModel):
    role: MessageRole
    text: str
    id: UUID
    created_at: datetime
