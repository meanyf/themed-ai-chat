import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from sqlalchemy.engine import make_url

from app.core.config import load_database_url, load_settings


class ConfigTests(TestCase):
    @patch.dict(os.environ, {}, clear=True)
    def test_database_uses_compose_values_without_chat_secrets(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            path.write_text("POSTGRES_PASSWORD=a@b:c\nPOSTGRES_PORT=5433\n")
            url = make_url(load_database_url(path))
            self.assertEqual((url.password, url.port), ("a@b:c", 5433))
            os.environ["DATABASE_URL"] = "postgresql+asyncpg://custom/chat"
            self.assertEqual(load_database_url(path), os.environ["DATABASE_URL"])

    @patch.dict(os.environ, {}, clear=True)
    def test_access_key_validation_and_secret_redaction(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / ".env"
            path.write_text("ACCESS_KEY=short\nGEMINI_API_KEY=secret-token\nGEMINI_MODEL=test-model\n")
            with self.assertRaisesRegex(ValueError, "ACCESS_KEY"):
                load_settings(path)
            os.environ["ACCESS_KEY"] = "valid_key-123"
            settings = load_settings(path)
            self.assertEqual(settings.access_key, "valid_key-123")
            self.assertNotIn("secret-token", repr(settings))
            self.assertNotIn(settings.access_key, repr(settings))
