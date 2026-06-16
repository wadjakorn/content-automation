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


class _FakeSession:
    """Mimics the slice of AsyncSession that create_item touches."""

    def __init__(self):
        self.added = []

    def add(self, obj):
        obj.id = 42  # real DB assigns on commit; fake assigns on add
        self.added.append(obj)

    async def commit(self):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False


def _fake_session_maker():
    return _FakeSession()


async def test_healthz():
    app = create_app(queue=_FakeQueue(), session_maker=_fake_session_maker)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://t") as c:
        r = await c.get("/healthz")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


async def test_create_item_persists_and_enqueues():
    q = _FakeQueue()
    app = create_app(queue=q, session_maker=_fake_session_maker)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://t") as c:
        r = await c.post("/items", json={"title": "idea", "pillar": "technology"})
    assert r.status_code == 202
    body = r.json()
    assert body["job_id"] == "job-1"
    assert body["item_id"] == 42
    assert q.jobs and q.jobs[0] == ("run_item_job", (42,))
