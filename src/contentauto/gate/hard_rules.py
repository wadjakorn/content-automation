"""Phase-0 hard-rules gate: keyword/regex only, no LLM, no retrieval.

Emits a schemas/lane-d-context.schema.json-shaped verdict so the full
Lane A–D cascade is a drop-in replacement later, not a rewrite.
"""
from __future__ import annotations

import re

from contentauto.models.verdicts import LaneDCheck, LaneDContextVerdict

# health/medical claim markers (TH + EN) — product claims => HOLD always (อย. legal exposure)
_HEALTH_PATTERNS = [
    r"รักษา(โรค)?",
    r"หาย(ขาด)?",
    r"ป้องกันโรค",
    r"ลดน้ำหนัก",
    r"เสริมภูมิ",
    r"\bcure[sd]?\b",
    r"\btreat(s|ment)?\b",
    r"\bprevents?\s+\w*\s*(disease|cancer|diabetes)",
    r"\bclinically proven\b",
]
_HEALTH_RE = re.compile("|".join(_HEALTH_PATTERNS), re.IGNORECASE)


def run_hard_rules(
    *, script: str, is_sponsored: bool, has_disclosure: bool
) -> LaneDContextVerdict:
    checks: list[LaneDCheck] = []
    risk = 0.0

    # 1) health/medical claim about a product -> HOLD
    m = _HEALTH_RE.search(script)
    if m:
        checks.append(
            LaneDCheck(
                type="sensitivity",
                hard=True,
                severity="high",
                evidence=f"health-claim marker: {m.group(0)!r}",
                action="hold",
            )
        )
        risk = max(risk, 0.9)
    else:
        checks.append(
            LaneDCheck(type="sensitivity", hard=True, severity="low", action="pass")
        )

    # 2) sponsored/gifted/affiliate without disclosure -> block
    if is_sponsored and not has_disclosure:
        checks.append(
            LaneDCheck(
                type="disclosure",
                hard=True,
                severity="high",
                evidence="is_sponsored=True and has_disclosure=False",
                action="block_until_disclosed",
            )
        )
        risk = max(risk, 0.7)
    else:
        checks.append(
            LaneDCheck(type="disclosure", hard=True, severity="low", action="pass")
        )

    return LaneDContextVerdict(checks=checks, reputational_risk=risk)
