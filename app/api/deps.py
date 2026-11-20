from fastapi import Depends, HTTPException, Request

from app.services.auth import AuthenticationError, AuthService
from app.services.chat import ChatService

SESSION_COOKIE = "session"


async def get_auth(request: Request) -> AuthService:
    return request.app.state.auth


async def get_chat(request: Request) -> ChatService:
    return request.app.state.chat


async def require_session(request: Request, auth: AuthService = Depends(get_auth)) -> None:
    token = request.cookies.get(SESSION_COOKIE)
    if not token:
        raise HTTPException(401, "Требуется вход.")
    try:
        await auth.authenticate(token)
    except AuthenticationError as exc:
        raise HTTPException(401, str(exc)) from exc
