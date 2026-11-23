import os
from unittest.mock import patch

import pytest
from sqlalchemy.engine import make_url

from app.core.config import load_database_url, load_settings


@pytest.fixture
def env_file(tmp_path):
    with patch.dict(os.environ, {}, clear=True):
        yield tmp_path / ".env"


@pytest.mark.parametrize("contents", ["", "POSTGRES_PASSWORD=\n"], ids=["missing", "empty"])
def test_database_requires_password_without_explicit_url(env_file, contents):
    env_file.write_text(contents)
    with pytest.raises(ValueError, match="POSTGRES_PASSWORD"):
        load_database_url(env_file)


def test_database_uses_compose_values_without_chat_secrets(env_file):
    env_file.write_text("POSTGRES_PASSWORD=a@b:c\nPOSTGRES_PORT=5433\n")
    url = make_url(load_database_url(env_file))
    assert (url.password, url.port) == ("a@b:c", 5433)
    custom_url = "postgresql+asyncpg://custom/chat"
    os.environ["DATABASE_URL"] = custom_url
    assert load_database_url(env_file) == custom_url


def test_access_key_validation_and_secret_redaction(env_file):
    env_file.write_text(
        "ACCESS_KEY=short\nGEMINI_API_KEY=secret-token\n"
        "GEMINI_MODEL=test-model\nPOSTGRES_PASSWORD=test-password\n"
    )
    with pytest.raises(ValueError, match="ACCESS_KEY"):
        load_settings(env_file)
    os.environ["ACCESS_KEY"] = "valid_key-123"
    settings = load_settings(env_file)
    assert settings.access_key == "valid_key-123"
    assert "secret-token" not in repr(settings)
    assert settings.access_key not in repr(settings)
