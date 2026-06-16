from __future__ import annotations

import abc
import datetime as dt
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class Capabilities:
    supports_native_schedule: bool
    requires_audit: bool
    can_fetch_comments: bool


class PlatformAdapter(abc.ABC):
    @property
    @abc.abstractmethod
    def capabilities(self) -> Capabilities: ...

    @abc.abstractmethod
    def schedule(self, *, video_id: str, publish_at: dt.datetime) -> dict[str, Any]: ...
