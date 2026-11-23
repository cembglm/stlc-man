"""Strict records for the ASRLab side of the IFARLAB verification lifecycle."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field, model_validator


SHA256 = r"^[a-f0-9]{64}$"


class SUTReference(BaseModel):
    sut_id: str = Field(..., min_length=1)
    version: str = Field(..., pattern=r"^[0-9]+\.[0-9]+\.[0-9]+(?:[-+][0-9A-Za-z.-]+)?$")
    source_sha256: str = Field(..., pattern=SHA256)


class SUTRelease(SUTReference):
    schema_version: Literal["1.0"] = "1.0"
    commit: str = Field(..., min_length=1)
    requirements_set_version: str = Field(..., min_length=1)
    build: Dict[str, Any] = Field(default_factory=dict)
    previous_version: Optional[str] = None
    fixes: List[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_defect_ids(self):
        invalid = [item for item in self.fixes if not __import__("re").fullmatch(r"D-[0-9]{4}-[0-9]{4}", item)]
        if invalid:
            raise ValueError("invalid defect identifiers in fixes: " + ", ".join(invalid))
        return self


class ApprovalDecision(str, Enum):
    APPROVED = "approved"
    REJECTED = "rejected"


class HumanApproval(BaseModel):
    approved_by: str = Field(..., min_length=1)
    approved_at: datetime
    decision: ApprovalDecision


class DefectRecord(BaseModel):
    defect_id: str = Field(..., pattern=r"^D-[0-9]{4}-[0-9]{4}$")
    sut_version: str
    requirement_id: str = Field(..., pattern=r"^QCR-[0-9]{3}$")
    test_case_id: str = Field(..., pattern=r"^[A-Z][A-Z0-9_]*_[0-9]{3}$")
    run_id: str = Field(..., pattern=r"^R-[0-9]{8}-[0-9]{4}$")
    scenario_id: Optional[str] = Field(None, pattern=r"^SC-[0-9]{3}$")
    fail_cause: Literal["sut"] = "sut"
    severity: Literal["low", "medium", "high", "critical"]
    symptom: str = Field(..., min_length=1)
    evidence: List[Dict[str, Any]] = Field(default_factory=list)
    proposed_patch: Optional[str] = None
    status: str = "open"


class PatchRecord(BaseModel):
    patch_id: str = Field(..., pattern=r"^P-[0-9]{4}-[0-9]{4}$")
    defect_id: str = Field(..., pattern=r"^D-[0-9]{4}-[0-9]{4}$")
    sut_version: str
    change_summary: str = Field(..., min_length=1)
    diff_sha256: str = Field(..., pattern=SHA256)
    approval: Optional[HumanApproval] = None
    applied_in_version: Optional[str] = None


class CriterionResult(BaseModel):
    satisfied: bool
    value: Any = None
    evidence: List[str] = Field(default_factory=list)


class RCReport(BaseModel):
    rc_id: str = Field(..., pattern=r"^RC-[0-9]+\.[0-9]+\.[0-9]+-[0-9]+$")
    sut_version: str
    exit_criteria: Dict[str, CriterionResult]
    requirement_verdicts: Dict[str, str]
    evidence_references: List[str] = Field(default_factory=list)
    closed_defects: List[str] = Field(default_factory=list)
    twin_fidelity_reference: str

    @model_validator(mode="after")
    def all_criteria_must_pass(self):
        failed = sorted(name for name, result in self.exit_criteria.items() if not result.satisfied)
        if failed:
            raise ValueError("RC report cannot be created; unsatisfied criteria: " + ", ".join(failed))
        return self


class PromotionRecord(BaseModel):
    promotion_id: str = Field(..., pattern=r"^PRM-[0-9]{4}-[0-9]{4}$")
    rc_id: str = Field(..., pattern=r"^RC-[0-9]+\.[0-9]+\.[0-9]+-[0-9]+$")
    rc_report_sha256: str = Field(..., pattern=SHA256)
    approval: HumanApproval
    target_cell: str = Field(..., min_length=1)

    @model_validator(mode="after")
    def approval_required(self):
        if self.approval.decision != ApprovalDecision.APPROVED:
            raise ValueError("promotion requires an explicit approved decision")
        return self


TEST_CASE_PREFIXES = {
    "INSP": "visual/quality inspection",
    "MOTION": "motion and reachability",
    "SAFETY": "safety constraints",
    "PERF": "performance and timing",
    "INTEG": "integration behavior",
}
