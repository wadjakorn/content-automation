"""Pure pipeline stages. The worker persists results to the DB between stages."""
from __future__ import annotations

import datetime as dt
from typing import Any

from contentauto.gate.hard_rules import run_hard_rules
from contentauto.llm.base import LLMClient
from contentauto.models.verdicts import LaneDContextVerdict
from contentauto.platforms.base import PlatformAdapter

# content pillar weights (CLAUDE.md: technology + ai/automation เน้น)
_PILLAR_WEIGHT = {
    "technology": 1.0,
    "ai": 1.0,
    "automation": 1.0,
    "gadgets": 0.7,
    "lifestyle": 0.4,
    "longevity": 0.4,
}

# actions that must stop the pipeline before publishing (CLAUDE.md hard rules)
_BLOCKING = {"hold", "block_until_disclosed"}


class GateBlocked(Exception):
    """Raised when a hard-rule verdict forbids auto-scheduling."""


def score_stage(*, pillar: str) -> float:
    return _PILLAR_WEIGHT.get(pillar.lower(), 0.5)


def plan_stage(llm: LLMClient, *, title: str, pillar: str) -> str:
    return llm.generate(
        f"Draft a content plan (angle, beats, hook) for a {pillar} video titled {title!r}."
    )


def script_stage(llm: LLMClient, *, plan: str) -> str:
    return llm.generate(f"Write a script body for this plan:\n{plan}")


def gate_stage(*, script: str, is_sponsored: bool, has_disclosure: bool) -> LaneDContextVerdict:
    return run_hard_rules(
        script=script, is_sponsored=is_sponsored, has_disclosure=has_disclosure
    )


def schedule_stage(
    adapter: PlatformAdapter,
    *,
    verdict: LaneDContextVerdict,
    video_id: str,
    publish_at: dt.datetime,
) -> dict[str, Any]:
    blocking = [c for c in verdict.checks if c.action in _BLOCKING]
    if blocking:
        reasons = ", ".join(f"{c.type}:{c.action}" for c in blocking)
        raise GateBlocked(reasons)
    return adapter.schedule(video_id=video_id, publish_at=publish_at)
