import pytest

from contentauto.models.content import ContentItem, ContentState
from contentauto.pipeline.worker import run_item, run_item_job
from contentauto.platforms.local import LocalAdapter


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


@pytest.mark.asyncio
async def test_run_item_job_commits_scheduled(session_maker):
    """End-to-end job path: seed item, run the production entrypoint, verify
    it opened its own session, advanced state, and committed."""
    async with session_maker() as s:
        item = ContentItem(
            title="M5 review", pillar="technology", state=ContentState.ready,
            script="clean review, no health claims", youtube_video_id="vid",
        )
        s.add(item)
        await s.commit()
        item_id = item.id

    ctx = {"session_maker": session_maker, "adapter": LocalAdapter(), "llm": _FakeLLM()}
    result = await run_item_job(ctx, item_id)
    assert result == {"blocked": False, "state": "scheduled"}

    async with session_maker() as s:  # fresh session → proves commit landed
        refreshed = await s.get(ContentItem, item_id)
        assert refreshed.state == ContentState.scheduled
        assert refreshed.score == 1.0  # technology pillar weight
        assert refreshed.scheduled_at is not None  # publish_at persisted to row
