"""phase0 tables

Revision ID: 34112c6b7c5f
Revises:
Create Date: 2026-06-16 18:08:45.419467

"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector

revision: str = "34112c6b7c5f"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

content_state = sa.Enum(
    "idea", "scripted", "filming", "editing", "ready", "scheduled", "published",
    name="content_state",
)


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    # The content_state enum type is created implicitly by the first create_table
    # that references it, and dropped by the matching drop_table in downgrade().
    op.create_table(
        "content_items",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=300), nullable=False),
        sa.Column("pillar", sa.String(length=40), nullable=False),
        sa.Column("state", content_state, nullable=False),
        sa.Column("score", sa.Float(), nullable=True),
        sa.Column("plan", sa.Text(), nullable=True),
        sa.Column("script", sa.Text(), nullable=True),
        sa.Column("youtube_video_id", sa.String(length=40), nullable=True),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_sponsored", sa.Boolean(), nullable=False),
        sa.Column("has_disclosure", sa.Boolean(), nullable=False),
    )
    op.create_table(
        "kb_entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("source", sa.String(length=80), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(1536), nullable=True),
    )
    op.create_table(
        "oauth_tokens",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("platform", sa.String(length=20), nullable=False, unique=True),
        sa.Column("ciphertext", sa.LargeBinary(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("oauth_tokens")
    op.drop_table("kb_entries")
    # Dropping content_items also drops the content_state enum type it owns.
    op.drop_table("content_items")
