from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_chat, require_session
from app.api.schemas.messages import MessageRequest, MessageResponse
from app.domain.message import Message
from app.services.chat import ChatService
from app.services.interfaces.llm_client import LLMError

router = APIRouter(prefix="/api/messages", dependencies=[Depends(require_session)])


@router.get("", response_model=list[MessageResponse])
async def history(chat: ChatService = Depends(get_chat)) -> list[Message]:
    return await chat.get_history()


@router.post("", response_model=MessageResponse)
async def send(body: MessageRequest, chat: ChatService = Depends(get_chat)) -> Message:
    try:
        return await chat.send_message(body.text)
    except LLMError as exc:
        raise HTTPException(502, "Не удалось получить ответ модели.") from exc
