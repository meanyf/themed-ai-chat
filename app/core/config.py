"""Настройки приложения из окружения и файла .env."""

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import dotenv_values
from sqlalchemy.engine import URL

ENV_FILE = Path(__file__).resolve().parents[2] / ".env"
DEFAULT_PROMPT = "Ты кулинарный помощник. Отвечай на вопросы о продуктах, рецептах и приготовлении еды."


@dataclass(frozen=True, slots=True)
class Settings:
    database_url: str = field(repr=False)
    access_key: str = field(repr=False)
    gemini_api_key: str = field(repr=False)
    gemini_model: str
    system_prompt: str


def _values(env_file: Path) -> dict[str, str]:
    values = {k: v for k, v in dotenv_values(env_file).items() if v is not None}
    return values | dict(os.environ)


def _database_url(values: dict[str, str]) -> str:
    if url := values.get("DATABASE_URL"):
        return url
    url = URL.create(
        "postgresql+asyncpg",
        username="chat",
        password=values.get("POSTGRES_PASSWORD") or "chat_local",
        host=values.get("POSTGRES_HOST") or "127.0.0.1",
        port=int(values.get("POSTGRES_PORT") or "5432"),
        database="chat",
    )
    return url.render_as_string(hide_password=False)


def load_database_url(env_file: Path = ENV_FILE) -> str:
    """Загружает параметры подключения для миграций."""
    return _database_url(_values(env_file))


def load_settings(env_file: Path = ENV_FILE) -> Settings:
    """Загружает настройки для запуска приложения."""
    values = _values(env_file)
    access_key = values.get("ACCESS_KEY", "")
    if not re.fullmatch(r"[A-Za-z0-9_-]{8,255}", access_key):
        raise ValueError("ACCESS_KEY должен содержать 8–255 латинских букв, цифр, дефисов или подчёркиваний.")
    for name in ("GEMINI_API_KEY", "GEMINI_MODEL"):
        if not values.get(name, "").strip():
            raise ValueError(f"Задайте {name}.")
    return Settings(
        database_url=_database_url(values),
        access_key=access_key,
        gemini_api_key=values["GEMINI_API_KEY"].strip(),
        gemini_model=values["GEMINI_MODEL"].strip(),
        system_prompt=values.get("SYSTEM_PROMPT", "").strip() or DEFAULT_PROMPT,
    )
