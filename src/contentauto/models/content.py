from __future__ import annotations

import datetime as _dt
import enum

from pgvector.sqlalchemy import Vector  # type: ignore[import-untyped]
from sqlalchemy import DateTime, Enum, Integer, LargeBinary, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class ContentState(enum.StrEnum):
    idea = "idea"
    scripted = "scripted"
    filming = "filming"
    editing = "editing"
    ready = "ready"
    scheduled = "scheduled"
    published = "published"


# explicit linear order — guard functions, no FSM library (spec: over-engineering for 7 states)
_ORDER: list[ContentState] = [
    ContentState.idea,
    ContentState.scripted,
    ContentState.filming,
    ContentState.editing,
    ContentState.ready,
    ContentState.scheduled,
    ContentState.published,
]


def next_state(state: ContentState) -> ContentState | None:
    i = _ORDER.index(state)
    return _ORDER[i + 1] if i + 1 < len(_ORDER) else None


def can_transition(frm: ContentState, to: ContentState) -> bool:
    if next_state(frm) != to:
        raise ValueError(f"illegal transition {frm.value} -> {to.value}")
    return True


class Base(DeclarativeBase):
    pass


class ContentItem(Base):
    __tablename__ = "content_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(300))
    pillar: Mapped[str] = mapped_column(String(40))
    state: Mapped[ContentState] = mapped_column(
        Enum(ContentState, name="content_state"), default=ContentState.idea
    )
    score: Mapped[float | None] = mapped_column(default=None)
    plan: Mapped[str | None] = mapped_column(Text, default=None)
    script: Mapped[str | None] = mapped_column(Text, default=None)
    youtube_video_id: Mapped[str | None] = mapped_column(String(40), default=None)
    scheduled_at: Mapped[_dt.datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    is_sponsored: Mapped[bool] = mapped_column(default=False)
    has_disclosure: Mapped[bool] = mapped_column(default=False)


class KbEntry(Base):
    __tablename__ = "kb_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    source: Mapped[str] = mapped_column(String(80))
    text: Mapped[str] = mapped_column(Text)
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1536), default=None)


class OAuthToken(Base):
    __tablename__ = "oauth_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    platform: Mapped[str] = mapped_column(String(20), unique=True)
    ciphertext: Mapped[bytes] = mapped_column(LargeBinary)  # Fernet blob — never plaintext
