import datetime as dt

import pytest

from contentauto.models.verdicts import LaneDContextVerdict
from contentauto.pipeline.stages import (
    GateBlocked,
    gate_stage,
    plan_stage,
    schedule_stage,
    score_stage,
    script_stage,
)


class _FakeLLM:
    def generate(self, prompt: str) -> str:
        return "PLAN" if prompt.lower().startswith("draft a content plan") else "SCRIPT BODY"

    def judge(self, prompt, schema):
        raise AssertionError("phase-0 gate is keyword-only, judge() not called")


class _FakeYT:
    def __init__(self):
        self.scheduled = None

    def schedule(self, *, video_id, publish_at):
        self.scheduled = (video_id, publish_at)
        return {"id": video_id}


def test_score_stage_weights_pillar():
    # technology pillar weighted higher than lifestyle
    assert score_stage(pillar="technology") > score_stage(pillar="lifestyle")


def test_plan_and_script_use_llm():
    assert plan_stage(_FakeLLM(), title="t", pillar="technology") == "PLAN"
    assert script_stage(_FakeLLM(), plan="PLAN") == "SCRIPT BODY"


def test_gate_stage_blocks_on_hold():
    v = gate_stage(script="ช่วยรักษาโรคได้", is_sponsored=False, has_disclosure=False)
    assert isinstance(v, LaneDContextVerdict)
    with pytest.raises(GateBlocked):
        schedule_stage(
            _FakeYT(), verdict=v, video_id="v",
            publish_at=dt.datetime(2026, 7, 1, tzinfo=dt.UTC),
        )


def test_schedule_stage_fires_when_clean():
    v = gate_stage(script="แกะกล่อง", is_sponsored=False, has_disclosure=False)
    yt = _FakeYT()
    when = dt.datetime(2026, 7, 1, tzinfo=dt.UTC)
    schedule_stage(yt, verdict=v, video_id="vid", publish_at=when)
    assert yt.scheduled == ("vid", when)
