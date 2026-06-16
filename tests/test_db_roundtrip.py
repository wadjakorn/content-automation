import pytest

from contentauto.models.content import ContentItem, ContentState


@pytest.mark.asyncio
async def test_insert_and_fetch_content_item(db_session):
    item = ContentItem(title="Test idea", pillar="technology", state=ContentState.idea)
    db_session.add(item)
    await db_session.flush()
    assert item.id is not None
    fetched = await db_session.get(ContentItem, item.id)
    assert fetched.state == ContentState.idea
    assert fetched.title == "Test idea"
