import datetime as dt

import pytest

from contentauto.platforms.base import Capabilities
from contentauto.platforms.stubs import TikTokAdapter
from contentauto.platforms.youtube import YouTubeAdapter


class _FakeVideos:
    def __init__(self):
        self.last_body = None

    def update(self, part, body):
        self.last_body = body

        class _Req:
            def execute(_self):
                return {"id": body["id"], "status": body["status"]}

        return _Req()


def test_youtube_capabilities():
    yt = YouTubeAdapter(videos_resource=_FakeVideos())
    assert yt.capabilities == Capabilities(
        supports_native_schedule=True, requires_audit=False, can_fetch_comments=True
    )


def test_schedule_sets_publish_at_and_private():
    fake = _FakeVideos()
    yt = YouTubeAdapter(videos_resource=fake)
    when = dt.datetime(2026, 7, 1, 9, 0, tzinfo=dt.UTC)
    out = yt.schedule(video_id="vid123", publish_at=when)
    assert fake.last_body["status"]["privacyStatus"] == "private"
    assert fake.last_body["status"]["publishAt"] == "2026-07-01T09:00:00+00:00"
    assert out["id"] == "vid123"


def test_tiktok_stub_raises():
    with pytest.raises(NotImplementedError):
        TikTokAdapter().schedule(video_id="x", publish_at=dt.datetime.now(dt.UTC))
