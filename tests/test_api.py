from httpx import ASGITransport, AsyncClient

from contentauto.api.app import create_app


class _FakeQueue:
    def __init__(self):
        self.jobs = []

    async def enqueue_job(self, fn, *args):
        self.jobs.append((fn, args))

        class _J:
            job_id = "job-1"

        return _J()


async def test_healthz():
    app = create_app(queue=_FakeQueue())
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://t") as c:
        r = await c.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


async def test_create_item_enqueues():
    q = _FakeQueue()
    app = create_app(queue=q)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://t") as c:
        r = await c.post("/items", json={"title": "idea", "pillar": "technology"})
    assert r.status_code == 202
    assert r.json()["job_id"] == "job-1"
    assert q.jobs and q.jobs[0][0] == "run_item"
