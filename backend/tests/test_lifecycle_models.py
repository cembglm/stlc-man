from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from models.ifarlab_lifecycle import PromotionRecord, RCReport


def test_rc_report_is_blocked_when_any_exit_criterion_fails():
    with pytest.raises(ValidationError, match="unsatisfied criteria"):
        RCReport(
            rc_id="RC-1.3.0-1", sut_version="1.3.0",
            exit_criteria={"mutation_score": {"satisfied": False, "value": 70}},
            requirement_verdicts={"QCR-001": "PASS"}, twin_fidelity_reference="FID-1",
        )


def test_promotion_requires_human_approval():
    base = dict(
        promotion_id="PRM-2026-0001", rc_id="RC-1.3.0-1",
        rc_report_sha256="a" * 64, target_cell="UR10e-QC-1",
    )
    with pytest.raises(ValidationError, match="explicit approved"):
        PromotionRecord(**base, approval={
            "approved_by": "engineer", "approved_at": datetime.now(timezone.utc), "decision": "rejected",
        })
    approved = PromotionRecord(**base, approval={
        "approved_by": "engineer", "approved_at": datetime.now(timezone.utc), "decision": "approved",
    })
    assert approved.approval.approved_by == "engineer"
