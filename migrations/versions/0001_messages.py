"""Создание таблицы сообщений."""

import sqlalchemy as sa
from alembic import op

revision = "0001_messages"
down_revision = None


def upgrade() -> None:
    op.create_table(
        "messages",
        sa.Column("id", sa.Uuid, primary_key=True),
        sa.Column("role", sa.Text, nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("role IN ('user', 'assistant')", name="messages_role"),
    )


def downgrade() -> None:
    op.drop_table("messages")
