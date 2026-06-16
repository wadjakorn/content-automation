from __future__ import annotations

import datetime as dt
from typing import Any

from contentauto.platforms.base import Capabilities, PlatformAdapter


class InstagramAdapter(PlatformAdapter):
    @property
    def capabilities(self) -> Capabilities:
        return Capabilities(False, True, False)  # no native schedule; needs Meta App Review

    def schedule(self, *, video_id: str, publish_at: dt.datetime) -> dict[str, Any]:
        raise NotImplementedError("Instagram adapter lands phase 2 (Meta App Review)")


class TikTokAdapter(PlatformAdapter):
    @property
    def capabilities(self) -> Capabilities:
        return Capabilities(False, True, False)  # draft-first while audit pending

    def schedule(self, *, video_id: str, publish_at: dt.datetime) -> dict[str, Any]:
        raise NotImplementedError("TikTok adapter lands phase 2 (app audit)")
