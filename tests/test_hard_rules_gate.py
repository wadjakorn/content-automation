from contentauto.gate.hard_rules import run_hard_rules
from contentauto.models.verdicts import LaneDContextVerdict


def test_health_claim_holds():
    v = run_hard_rules(
        script="อาหารเสริมตัวนี้ช่วยรักษาโรคเบาหวานได้",
        is_sponsored=False,
        has_disclosure=False,
    )
    assert isinstance(v, LaneDContextVerdict)
    hold = [c for c in v.checks if c.action == "hold"]
    assert hold and hold[0].type == "sensitivity" and hold[0].hard is True


def test_sponsored_without_disclosure_blocks():
    v = run_hard_rules(script="รีวิวหูฟังรุ่นใหม่", is_sponsored=True, has_disclosure=False)
    blocked = [c for c in v.checks if c.action == "block_until_disclosed"]
    assert blocked and blocked[0].type == "disclosure" and blocked[0].hard is True


def test_clean_script_passes():
    v = run_hard_rules(script="แกะกล่องคีย์บอร์ดกลไก", is_sponsored=False, has_disclosure=False)
    assert all(c.action == "pass" for c in v.checks)
    assert v.reputational_risk == 0.0


def test_sponsored_with_disclosure_passes():
    v = run_hard_rules(script="รีวิวหูฟัง #ได้รับสปอนเซอร์", is_sponsored=True, has_disclosure=True)
    assert all(c.action != "block_until_disclosed" for c in v.checks)
