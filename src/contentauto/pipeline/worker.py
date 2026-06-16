"""arq worker: run_item job + WorkerSettings factory.

Import safety
-------------
WorkerSettings is NOT a top-level class — it is built lazily by
``build_worker_settings()``.  This means ``import contentauto.pipeline.worker``
(and ``from contentauto.pipeline.worker import run_item``) succeed with NO env
vars present, which is required for pytest collection.

The arq CLI is invoked as::

    arq contentauto.pipeline.worker.build_worker_settings
               ↑ arq accepts a callable that returns a class

or via the returned class::

    settings = build_worker_settings()
    # arq.worker.run_worker(settings)
"""
from __future__ import annotations

import datetime as dt
from typing import Any

from contentauto.models.content import ContentItem, ContentState
from contentauto.pipeline.stages import (
    GateBlocked,
    gate_stage,
    schedule_stage,
    score_stage,
)


async def run_item(ctx: dict[str, Any], item_id: int) -> dict[str, Any]:
    """arq job: score → gate → schedule one ContentItem."""
    session = ctx["session"]
    adapter = ctx["adapter"]

    item = await session.get(ContentItem, item_id)
    if item is None:
        return {"error": "not found"}

    item.score = score_stage(pillar=item.pillar)
    verdict = gate_stage(
        script=item.script or "",
        is_sponsored=item.is_sponsored,
        has_disclosure=item.has_disclosure,
    )
    publish_at: dt.datetime = item.scheduled_at or dt.datetime.now(dt.UTC)
    try:
        schedule_stage(
            adapter,
            verdict=verdict,
            video_id=item.youtube_video_id or "",
            publish_at=publish_at,
        )
    except GateBlocked as exc:
        await session.flush()
        return {"blocked": True, "reason": str(exc)}

    item.scheduled_at = publish_at
    item.state = ContentState.scheduled
    await session.flush()
    return {"blocked": False, "state": item.state.value}


async def run_item_job(ctx: dict[str, Any], item_id: int) -> dict[str, Any]:
    """Production arq entrypoint: open a session, build per-job ctx, commit.

    ``run_item`` stays session-agnostic (tests inject their own session); this
    wrapper owns the session lifecycle and commit so a real job persists.
    """
    session_maker = ctx["session_maker"]
    async with session_maker() as session:
        job_ctx = {
            "session": session,
            "adapter": ctx["adapter"],
            "llm": ctx.get("llm"),
        }
        result = await run_item(job_ctx, item_id)
        await session.commit()
    return result


# ---------------------------------------------------------------------------
# arq startup / WorkerSettings — resolved LAZILY so bare import needs no envs
# ---------------------------------------------------------------------------

async def startup(ctx: dict[str, Any]) -> None:
    """Populate shared resources in the arq worker context."""
    from contentauto.config import get_settings
    from contentauto.db import session_factory
    from contentauto.llm.claude import ClaudeClient

    from contentauto.platforms.local import LocalAdapter

    s = get_settings()
    ctx["session_maker"] = session_factory()
    ctx["llm"] = ClaudeClient(api_key=s.anthropic_api_key, model=s.anthropic_model)
    # No stored OAuth creds yet → LocalAdapter (no external API). Swap for
    # YouTubeAdapter built from decrypted creds once OAuth routes land.
    ctx["adapter"] = LocalAdapter()


def build_worker_settings() -> type:
    """Return a fresh WorkerSettings class with redis_settings resolved now.

    Call this only at worker-launch time (env vars must be set).
    The module-level bare import does NOT call this function, so pytest
    collection works without any environment variables.
    """
    from arq.connections import RedisSettings

    from contentauto.config import get_settings

    class WorkerSettings:
        functions = [run_item_job]
        on_startup = startup
        redis_settings = RedisSettings.from_dsn(get_settings().redis_url)

    return WorkerSettings
