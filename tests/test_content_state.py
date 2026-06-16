import pytest

from contentauto.models.content import ContentState, can_transition, next_state


def test_legal_forward_transition():
    assert can_transition(ContentState.idea, ContentState.scripted)
    assert next_state(ContentState.editing) == ContentState.ready


def test_illegal_skip_raises():
    with pytest.raises(ValueError, match="illegal transition"):
        can_transition(ContentState.idea, ContentState.published)


def test_terminal_state_has_no_next():
    assert next_state(ContentState.published) is None
