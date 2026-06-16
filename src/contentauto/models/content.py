from __future__ import annotations

import enum


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
