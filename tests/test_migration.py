import sqlite3
from io import StringIO
from unittest import TestCase

from alembic import command
from alembic.config import Config


class MigrationTests(TestCase):
    def test_initial_migration_allows_long_replies_and_rejects_unknown_roles(self):
        output = StringIO()
        config = Config("alembic.ini", output_buffer=output)
        command.upgrade(config, "head", sql=True)
        db = sqlite3.connect(":memory:")
        self.addCleanup(db.close)
        db.executescript(output.getvalue())
        insert = "INSERT INTO messages (id, role, text, created_at) VALUES (?, ?, ?, CURRENT_TIMESTAMP)"
        db.execute(insert, ("1", "assistant", "a" * 501))
        with self.assertRaises(sqlite3.IntegrityError):
            db.execute(insert, ("2", "unknown", "text"))

    def test_session_hash_is_unique(self):
        output = StringIO()
        command.upgrade(Config("alembic.ini", output_buffer=output), "head", sql=True)
        db = sqlite3.connect(":memory:")
        self.addCleanup(db.close)
        db.executescript(output.getvalue())
        insert = "INSERT INTO sessions (token_hash, expires_at) VALUES (?, CURRENT_TIMESTAMP)"
        db.execute(insert, ("a" * 64,))
        with self.assertRaises(sqlite3.IntegrityError):
            db.execute(insert, ("a" * 64,))
