from __future__ import annotations

import datetime as dt
from typing import Any

from contentauto.platforms.base import Capabilities, PlatformAdapter


class YouTubeAdapter(PlatformAdapter):
    """Official YouTube Data API v3 only — no scraping/UI automation (CLAUDE.md)."""

    def __init__(self, videos_resource: Any) -> None:
        # videos_resource is a google-api-python-client dynamic Resource;
        # it has no stubs, so Any is correct here — do not tighten this seam.
        self._videos: Any = videos_resource

    @property
    def capabilities(self) -> Capabilities:
        return Capabilities(
            supports_native_schedule=True,  # status.publishAt offload
            requires_audit=False,
            can_fetch_comments=True,
        )

    def schedule(self, *, video_id: str, publish_at: dt.datetime) -> dict[str, Any]:
        body: dict[str, Any] = {
            "id": video_id,
            "status": {"privacyStatus": "private", "publishAt": publish_at.isoformat()},
        }
        result: dict[str, Any] = self._videos.update(part="status", body=body).execute()
        return result
