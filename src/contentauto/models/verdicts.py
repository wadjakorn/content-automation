# src/contentauto/models/verdicts.py
"""Pydantic v2 mirrors of schemas/*.json (JSON Schema draft 2020-12).

Hand-written, kept in sync by tests/test_verdicts_match_schema.py.
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

# ---- Lane A: policy / safety ----
LaneACategoryType = Literal[
    "identity_attack", "hate_speech", "slur", "threat", "dehumanization"
]
LaneAStance = Literal["discussing", "quoting", "criticizing", "endorsing", "attacking"]


class LaneACategory(BaseModel):
    type: LaneACategoryType
    stance: LaneAStance
    score: float = Field(ge=0, le=1)
    evidence: str | None = None
    target_group: str | None = None


class LaneAVerdict(BaseModel):
    surface: Literal["script", "transcript", "ocr", "thumbnail", "title"]
    verdict: Literal["pass", "flag", "hold"]
    categories: list[LaneACategory]
    suggested_fix: str | None = None
    requires_human: bool


# ---- Lane B: tone / brand (advisory only) ----
class LaneBAdvisory(BaseModel):
    surface: Literal["script", "transcript", "ocr", "title", "thumbnail"]
    pattern: Literal[
        "condescension", "punching_down", "gatekeeping",
        "unwarranted_absolutism", "sneer",
    ]
    severity: Literal["low", "medium"]
    span: str | None = None
    why_it_risks: str | None = None
    on_brand_alt: str | None = None
    decision: Literal["advisory"] = "advisory"


# ---- Lane C: fact-check ----
class LaneCEvidence(BaseModel):
    tier: Literal[1, 2, 3]
    url: str
    snippet: str | None = None


class LaneCFactCheck(BaseModel):
    surface: Literal["script", "transcript"]
    claim: str
    type: Literal[
        "spec_numeric", "price", "comparative", "superlative",
        "causal_technical", "temporal",
    ]
    verdict: Literal["SUPPORTED", "REFUTED", "NOT_ENOUGH_INFO"]
    evidence: list[LaneCEvidence] = Field(default_factory=list)
    correct_value: str | None = None
    confidence: float | None = Field(default=None, ge=0, le=1)
    requires_human: bool


# ---- Lane D: context / timing (the phase-0 gate emits this) ----
LaneDCheckType = Literal["disclosure", "sensitivity", "consistency"]
LaneDAction = Literal[
    "pass", "advisory", "suggest_reschedule", "block_until_disclosed", "hold"
]


class LaneDCheck(BaseModel):
    type: LaneDCheckType
    hard: bool
    severity: Literal["low", "medium", "high"]
    evidence: str | None = None
    action: LaneDAction


class LaneDContextVerdict(BaseModel):
    checks: list[LaneDCheck]
    reputational_risk: float = Field(ge=0, le=1)


# ---- Post-publish monitor ----
# proposed_actions items are schema-constrained to specific enum values
MonitorProposedAction = Literal[
    "log_only",
    "draft_pinned_correction",
    "draft_response",
    "suggest_pin",
    "suggest_edit_metadata",
    "suggest_unlist",
]


class MonitorSnapshot(BaseModel):
    item_id: str
    platform: Literal["youtube", "instagram", "tiktok"]
    sampled_at: str
    since_publish_min: int = Field(ge=0)
    signals: dict[str, object]
    alert_tier: Literal["L0", "L1", "L2", "L3"]
    proposed_actions: list[MonitorProposedAction] = Field(default_factory=list)
    requires_human: bool | None = None
    baseline_mode: Literal["learning", "active"] | None = None
