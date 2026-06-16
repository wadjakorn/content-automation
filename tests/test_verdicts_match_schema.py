# tests/test_verdicts_match_schema.py
import json
from pathlib import Path

import jsonschema
import pytest

from contentauto.models.verdicts import (
    LaneAVerdict,
    LaneBAdvisory,
    LaneCFactCheck,
    LaneDContextVerdict,
    MonitorSnapshot,
)

SCHEMA_DIR = Path(__file__).resolve().parents[1] / "schemas"


def _load(name: str) -> dict:
    return json.loads((SCHEMA_DIR / name).read_text())


CASES = [
    (
        "lane-d-context.schema.json",
        LaneDContextVerdict(
            checks=[{"type": "disclosure", "hard": True, "severity": "high",
                     "action": "block_until_disclosed", "evidence": "no #ad"}],
            reputational_risk=0.4,
        ),
    ),
    (
        "lane-a-verdict.schema.json",
        LaneAVerdict(
            surface="script", verdict="pass", categories=[], requires_human=False,
        ),
    ),
    (
        "lane-b-advisory.schema.json",
        LaneBAdvisory(
            surface="script", pattern="condescension", severity="low", decision="advisory",
        ),
    ),
    (
        "lane-c-factcheck.schema.json",
        LaneCFactCheck(
            surface="script", claim="X has 8GB RAM", type="spec_numeric",
            verdict="NOT_ENOUGH_INFO", requires_human=True,
        ),
    ),
    (
        "monitor-snapshot.schema.json",
        MonitorSnapshot(
            item_id="abc", platform="youtube", sampled_at="2026-06-16T00:00:00Z",
            since_publish_min=10, signals={}, alert_tier="L0",
        ),
    ),
]


@pytest.mark.parametrize("schema_file,model", CASES)
def test_model_dump_validates_against_schema(schema_file, model):
    schema = _load(schema_file)
    instance = model.model_dump(mode="json", exclude_none=True)
    jsonschema.validate(instance, schema)  # raises if drift
