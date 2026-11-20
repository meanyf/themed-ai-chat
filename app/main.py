from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.routes import auth, messages
from app.core.config import load_settings
from app.db.session import database_sessions
from app.integrations.gemini import GeminiClient
from app.repositories.postgres_message_repository import PostgresMessageRepository
from app.repositories.postgres_session_repository import PostgresSessionRepository
from app.services.auth import AuthService
from app.services.chat import ChatService


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = load_settings()
    async with database_sessions(settings.database_url) as sessions:
        app.state.auth = AuthService(PostgresSessionRepository(sessions), settings.access_key)
        llm = GeminiClient(api_key=settings.gemini_api_key, model=settings.gemini_model,
                           system_prompt=settings.system_prompt)
        app.state.chat = ChatService(PostgresMessageRepository(sessions), llm)
        yield


app = FastAPI(lifespan=lifespan)
app.include_router(auth.router)
app.include_router(messages.router)

frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
