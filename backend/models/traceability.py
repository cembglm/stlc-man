"""Versioned ASRLab/IFARLAB traceability contracts."""

from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, field_validator, model_validator


class RequirementType(str, Enum):
    FUNCTIONAL = "functional"
    NON_FUNCTIONAL = "non_functional"


class Operator(str, Enum):
    EQ = "=="
    NE = "!="
    LT = "<"
    LE = "<="
    GT = ">"
    GE = ">="
    IN = "in"
    NOT_IN = "not_in"


class AcceptanceCriterion(BaseModel):
    rule_id: Optional[str] = None
    metric: str = Field(..., min_length=1)
    operator: Operator
    threshold: Union[Decimal, str, List[Union[Decimal, str]]]
    unit: Optional[str] = None
    severity: str = "mandatory"

    @field_validator("unit")
    def normalize_unit(cls, value):
        return value.strip() if isinstance(value, str) and value.strip() else None


class Requirement(BaseModel):
    id: str = Field(..., min_length=1, pattern=r"^(?:FR|NFR)-[0-9]{3}$")
    version: str = Field(..., min_length=1)
    type: RequirementType
    text: str = Field(..., min_length=1)
    acceptance: List[AcceptanceCriterion] = Field(default_factory=list)
    acceptance_review_required: bool = False
    source_references: List[str] = Field(default_factory=list)
    related_artifacts: List[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def flag_unmeasurable(self):
        self.acceptance_review_required = bool(self.acceptance_review_required or not self.acceptance)
        return self


class RequirementSet(BaseModel):
    schema_version: str = "1.0"
    requirements_set_version: str = Field(..., min_length=1)
    requirements: List[Requirement]
    model_config = {"json_schema_extra": {"examples": [{
        "schema_version": "1.0", "requirements_set_version": "2026-11-18",
        "requirements": [{"id": "NFR-001", "version": "1.0", "type": "non_functional", "text": "The robot shall complete the trajectory within 20 seconds.", "acceptance": [{"metric": "trajectory_duration", "operator": "<=", "threshold": 20, "unit": "s"}]}],
    }]}}

    @field_validator("requirements")
    def unique_ids(cls, value):
        ids = [item.id for item in value]
        if len(ids) != len(set(ids)):
            raise ValueError("requirement identifiers must be unique")
        return value


class GenerationProvenance(BaseModel):
    provider: Optional[str] = None
    model: Optional[str] = None
    model_version: Optional[str] = None
    temperature: Optional[Decimal] = None
    prompt_sha256: Optional[str] = Field(None, pattern=r"^[a-f0-9]{64}$")
    generated_at: datetime


class CodeQuality(BaseModel):
    validator: str = "not_recorded"
    lint: str = "not_recorded"
    syntax: str = "not_recorded"
    verdict: str = "not_recorded"
    validator_version: Optional[str] = None
    validated_at: Optional[datetime] = None
    findings: List[Dict[str, Any]] = Field(default_factory=list)


class ManifestTest(BaseModel):
    function: str = Field(..., min_length=1)
    test_case_id: str = Field(..., min_length=1, pattern=r"^[A-Z][A-Z0-9_]*_[0-9]{3}$")
    requirements: List[str] = Field(default_factory=list)
    expected_outcome: Optional[str] = None
    expected_reason: Optional[str] = None
    oracle: Dict[str, Any] = Field(default_factory=dict)


class SubmissionManifest(BaseModel):
    schema_version: str = "1.0"
    submission_id: str = Field(..., pattern=r"^S-[0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{4}$")
    revision: int = Field(1, ge=1)
    code_sha256: str = Field(..., pattern=r"^[a-f0-9]{64}$")
    requirements_set_version: str
    contract_sha256: str = Field(..., pattern=r"^[a-f0-9]{64}$")
    generation: GenerationProvenance
    code_quality: CodeQuality
    tests: List[ManifestTest]


class MetricValue(BaseModel):
    value: Optional[Union[Decimal, str, bool]] = None
    unit: Optional[str] = None
    source: Optional[str] = None
    run_id: Optional[str] = None
    status: str = "measured"

    @model_validator(mode="after")
    def unavailable_has_no_value(self):
        if self.status == "unavailable" and self.value is not None:
            raise ValueError("unavailable measurements must use a null value")
        if self.status == "measured" and self.value is None:
            raise ValueError("measured measurements require a value")
        return self


class EvidenceReference(BaseModel):
    evidence_id: str
    kind: str
    sha256: Optional[str] = Field(None, pattern=r"^[a-f0-9]{64}$")
    external_reference: Optional[str] = None


class ExternalTestResult(BaseModel):
    test_case_id: str
    status: str
    assertion_result: Optional[str] = None
    robot_verdict: Optional[str] = None
    external_verdict: Optional[str] = None
    admission: Optional[str] = None
    validity_status: Optional[str] = None
    code_quality_verdict: Optional[str] = None
    metrics: Dict[str, MetricValue] = Field(default_factory=dict)
    evidence: List[EvidenceReference] = Field(default_factory=list)
    validity: Dict[str, Any] = Field(default_factory=dict)
    verdict_explanation: Optional[str] = None


class IFARLABResult(BaseModel):
    schema_version: str = "1.0"
    submission_id: str = Field(..., pattern=r"^S-[0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{4}$")
    run_id: str = Field(..., pattern=r"^R-[0-9]{8}-[0-9]{4}$")
    requirements_set_version: str
    code_sha256: str = Field(..., pattern=r"^[a-f0-9]{64}$")
    contract_sha256: str = Field(..., pattern=r"^[a-f0-9]{64}$")
    executed_at: datetime
    external_system: str = "IFARLAB"
    environment: Dict[str, Any] = Field(default_factory=dict)
    submission_status: Optional[str] = None
    code_quality: Optional[CodeQuality] = None
    test_results: List[ExternalTestResult]
    model_config = {"json_schema_extra": {"examples": [{
        "schema_version": "1.0", "submission_id": "S-2026-11-18-0042", "run_id": "R-20261118-0197",
        "requirements_set_version": "2026-11-18", "code_sha256": "a" * 64, "contract_sha256": "b" * 64,
        "executed_at": "2026-11-18T12:00:00Z", "external_system": "IFARLAB",
        "environment": {"simulator": "Gazebo", "image": "ros2-exec-harness:0.3.2"},
        "test_results": [{"test_case_id": "MOTION_004", "status": "completed", "assertion_result": "PASS", "robot_verdict": "FAIL", "metrics": {"trajectory_duration": {"value": 23.4, "unit": "s"}, "collision_count": {"value": 0, "unit": "count"}}, "evidence": [{"evidence_id": "E-0197", "kind": "rosbag", "sha256": "c" * 64}], "validity": {"trustworthy": True}}],
    }]}}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
