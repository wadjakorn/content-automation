import pytest

from contentauto.models.content import ContentItem, ContentState
from contentauto.pipeline.worker import run_item


class _FakeLLM:
    def generate(self, prompt: str) -> str:
        return "PLAN" if "plan" in prompt.lower() else "SCRIPT"

    def judge(self, prompt, schema):
        raise AssertionError


class _FakeYT:
    def schedule(self, *, video_id, publish_at):
        return {"id": video_id}


@pytest.mark.asyncio
async def test_run_item_blocks_on_health_claim(db_session):
    item = ContentItem(
        title="อาหารเสริม", pillar="longevity", state=ContentState.ready,
        script="ช่วยรักษาโรคเบาหวาน", youtube_video_id="vid",
    )
    db_session.add(item)
    await db_session.flush()
    ctx = {"session": db_session, "llm": _FakeLLM(), "adapter": _FakeYT()}
    result = await run_item(ctx, item.id)
    assert result["blocked"] is True
    refreshed = await db_session.get(ContentItem, item.id)
    assert refreshed.state == ContentState.ready  # not advanced to scheduled
