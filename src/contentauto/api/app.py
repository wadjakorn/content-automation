"""Phase-0 FastAPI app: healthz + item create/enqueue.

create_app(queue) — tests inject a fake queue (used directly; lifespan is not
run under ASGITransport). The container uses the module-level `app` below with
queue=None, which lazily builds a real arq Redis pool on startup. Importing this
module requires NO env vars (settings/Redis resolve only inside the lifespan).
"""
from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel


class NewItem(BaseModel):
    title: str
    pillar: str


def create_app(queue: Any | None = None) -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        if queue is None:
            from arq import create_pool
            from arq.connections import RedisSettings
            from redis.exceptions import RedisError

            from contentauto.config import get_settings

            # Resilient startup: if Redis is unreachable, the app still boots
            # (so /healthz works in dev). /items returns 503 until the queue is up.
            try:
                app.state.queue = await create_pool(
                    RedisSettings.from_dsn(get_settings().redis_url)
                )
            except (OSError, RedisError):
                app.state.queue = None
        else:
            app.state.queue = queue
        yield

    app = FastAPI(title="content-automation phase-0", lifespan=lifespan)

    @app.get("/healthz")
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    @app.post("/items", status_code=202)
    async def create_item(body: NewItem, request: Request) -> dict[str, Any]:
        q = queue if queue is not None else getattr(request.app.state, "queue", None)
        if q is None:
            raise HTTPException(status_code=503, detail="job queue unavailable (Redis down)")
        # Phase-0: enqueue by title placeholder. Real impl persists a
        # ContentItem(state=idea) first and enqueues its id (follow-up).
        job = await q.enqueue_job("run_item", body.title)
        return {"job_id": job.job_id, "title": body.title}

    return app


app = create_app()
