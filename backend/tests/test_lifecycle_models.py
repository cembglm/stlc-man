from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from models.ifarlab_lifecycle import MutantRequest, MutantResult, PromotionRecord, RCReport


def test_rc_report_records_unsatisfied_exit_criteria_without_claiming_eligibility():
    report = RCReport(
        rc_id="RC-1.3.0-1", sut_version="1.3.0",
        exit_criteria={"mutation_score": {"satisfied": False, "value": 70}},
        requirement_verdicts={"QCR-001": "PASS"}, twin_fidelity_reference="FID-1",
    )
    assert report.eligible is False


def test_rc_report_without_fidelity_is_out_of_scope_and_ineligible():
    report = RCReport(
        rc_id="RC-1.3.0-1", sut_version="1.3.0",
        exit_criteria={"mandatory_qcr": {"satisfied": True}},
        requirement_verdicts={"QCR-001": "PASS"},
    )
    assert report.eligible is False


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


def test_mutant_contracts_require_deterministic_selection_and_kill_evidence():
    request = MutantRequest(
        mutant_id="M-2026-0001", base_version="1.2.0", mutation_type="joint_limit",
        diff_text="- old\n+ new", diff_sha256="a" * 64,
        test_case_ids=["REF_001"], selection={"method": "risk", "seed": 7},
    )
    assert request.selection["seed"] == 7
    with pytest.raises(ValidationError, match="killed_by"):
        MutantResult(mutant_id="M-2026-0001", outcome="killed")
    assert MutantResult(
        mutant_id="M-2026-0001", outcome="killed", killed_by=["REF_001"],
        run_ids=["R-20261125-0001"],
    ).outcome == "killed"
