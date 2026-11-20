"""Создание таблицы сессий."""

import sqlalchemy as sa
from alembic import op

revision = "0002_sessions"
down_revision = "0001_messages"


def upgrade() -> None:
    op.create_table(
        "sessions",
        sa.Column("token_hash", sa.String(64), primary_key=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("sessions")
