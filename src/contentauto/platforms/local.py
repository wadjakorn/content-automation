from __future__ import annotations

import datetime as dt
from typing import Any

from contentauto.platforms.base import Capabilities, PlatformAdapter


class LocalAdapter(PlatformAdapter):
    """Dev/no-op adapter for local end-to-end runs before YouTube OAuth lands.

    Touches no external API — records the intended schedule and returns it.
    Swapped for YouTubeAdapter once stored OAuth creds exist.
    """

    @property
    def capabilities(self) -> Capabilities:
        return Capabilities(
            supports_native_schedule=True,
            requires_audit=False,
            can_fetch_comments=False,
        )

    def schedule(self, *, video_id: str, publish_at: dt.datetime) -> dict[str, Any]:
        return {
            "scheduled": True,
            "video_id": video_id,
            "publish_at": publish_at.isoformat(),
        }
