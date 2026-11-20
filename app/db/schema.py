import sqlalchemy as sa

metadata = sa.MetaData()
messages = sa.Table(
    "messages",
    metadata,
    sa.Column("id", sa.Uuid, primary_key=True),
    sa.Column("role", sa.Text, nullable=False),
    sa.Column("text", sa.Text, nullable=False),
    sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    sa.CheckConstraint("role IN ('user', 'assistant')", name="messages_role"),
)
