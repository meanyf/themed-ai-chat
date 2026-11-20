from fastapi import APIRouter, Depends, HTTPException, Request, Response

from app.api.deps import SESSION_COOKIE, get_auth
from app.api.schemas.auth import LoginRequest
from app.services.auth import AuthenticationError, AuthService

router = APIRouter(prefix="/api/auth")


@router.post("/login", status_code=204)
async def login(body: LoginRequest, request: Request, response: Response,
                auth: AuthService = Depends(get_auth)) -> None:
    try:
        token = await auth.login(body.key.get_secret_value())
    except AuthenticationError as exc:
        raise HTTPException(401, str(exc)) from exc
    response.set_cookie(SESSION_COOKIE, token, httponly=True, samesite="strict",
                        secure=request.url.scheme == "https", path="/api")


@router.post("/logout", status_code=204)
async def logout(request: Request, response: Response, auth: AuthService = Depends(get_auth)) -> None:
    if token := request.cookies.get(SESSION_COOKIE):
        await auth.logout(token)
    response.delete_cookie(SESSION_COOKIE, path="/api", httponly=True, samesite="strict",
                           secure=request.url.scheme == "https")
