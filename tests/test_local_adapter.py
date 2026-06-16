import datetime as dt

from contentauto.platforms.local import LocalAdapter


def test_local_adapter_schedule_echoes():
    a = LocalAdapter()
    when = dt.datetime(2026, 6, 16, 12, 0, tzinfo=dt.UTC)
    out = a.schedule(video_id="vid123", publish_at=when)
    assert out == {
        "scheduled": True,
        "video_id": "vid123",
        "publish_at": when.isoformat(),
    }


def test_local_adapter_capabilities():
    caps = LocalAdapter().capabilities
    assert caps.supports_native_schedule is True
    assert caps.requires_audit is False
