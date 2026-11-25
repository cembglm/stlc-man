"""Versioned ASRLab/IFARLAB traceability contracts."""

from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field, field_validator, model_validator


class RequirementType(str, Enum):
    FUNCTIONAL = "functional"
    NON_FUNCTIONAL = "non_functional"
    UNCLASSIFIED = "unclassified"


class RequirementStatus(str, Enum):
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    RETIRED = "retired"


class ExecutionScope(str, Enum):
    DIGITAL_TWIN = "digital_twin"
    PHYSICAL_TWIN = "physical_twin"
    LOCAL = "local"
    SIMULATION = "simulation"
    MOCK = "mock"
    UNKNOWN = "unknown"


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
    clock: Optional[str] = None
    severity: str = "mandatory"

    @field_validator("unit")
    def normalize_unit(cls, value):
        return value.strip() if isinstance(value, str) and value.strip() else None


class Requirement(BaseModel):
    id: str = Field(..., min_length=1, pattern=r"^(?:(?:FR|NFR|REQ)-[A-Z0-9][A-Z0-9_.-]*|QCR-[0-9]{3})$")
    version: str = Field(..., min_length=1)
    type: RequirementType
    text: str = Field(..., min_length=1)
    acceptance: List[AcceptanceCriterion] = Field(default_factory=list)
    priority: Optional[Literal["mandatory", "desired"]] = None
    expected_outcome: Optional[str] = Field(None, pattern=r"^(reach|reject|accept)$")
    expected_reason: Optional[str] = None
    oracle: Dict[str, Any] = Field(default_factory=dict)
    acceptance_review_required: bool = False
    source_references: List[str] = Field(default_factory=list)
    related_artifacts: List[str] = Field(default_factory=list)
    source_artifact: Optional[str] = None
    source_artifact_sha256: Optional[str] = Field(None, pattern=r"^[a-f0-9]{64}$")
    digital_twin_ids: List[str] = Field(default_factory=list)
    status: RequirementStatus = RequirementStatus.ACTIVE
    applicable: bool = True
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    supersedes_version: Optional[str] = None

    @model_validator(mode="after")
    def flag_unmeasurable(self):
        if self.id.startswith("QCR-") and self.priority is None:
            raise ValueError("QCR priority is required and must be mandatory or desired")
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

    @model_validator(mode="after")
    def qcr_set_contract(self):
        if self.requirements_set_version.startswith("QCR-"):
            if not __import__("re").fullmatch(r"QCR-[0-9]{4}-[0-9]{2}-[0-9]{2}", self.requirements_set_version):
                raise ValueError("QCR requirements_set_version must use QCR-YYYY-MM-DD")
            invalid = [item.id for item in self.requirements if not item.id.startswith("QCR-")]
            if invalid:
                raise ValueError("QCR sets may contain only QCR-NNN identifiers")
        return self


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
    test_case_version: str = "1.0"
    scenario_id: Optional[str] = None
    requirements: List[str] = Field(default_factory=list)
    requirement_versions: Dict[str, str] = Field(default_factory=dict)
    expected_outcome: Optional[str] = None
    expected_reason: Optional[str] = None
    oracle: Dict[str, Any] = Field(default_factory=dict)


class ManifestSUT(BaseModel):
    sut_id: str = Field(..., min_length=1)
    version: str = Field(..., min_length=1)
    commit: str = Field(..., min_length=1)
    source_sha256: str = Field(..., pattern=r"^[a-f0-9]{64}$")


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
    sut: Optional[ManifestSUT] = None
    project_id: Optional[str] = None
    session_id: Optional[str] = None


class ExecutionEnvironment(BaseModel):
    scope: ExecutionScope = ExecutionScope.UNKNOWN
    environment_id: Optional[str] = None
    digital_twin_id: Optional[str] = None
    registry_reference: Optional[str] = None
    provenance_sha256: Optional[str] = Field(None, pattern=r"^[a-f0-9]{64}$")
    simulator: Optional[str] = None
    image: Optional[str] = None
    model_config = {"extra": "allow"}

    @property
    def qualifies_as_digital_twin(self) -> bool:
        return bool(
            self.scope == ExecutionScope.DIGITAL_TWIN
            and self.environment_id
            and self.digital_twin_id
            and (self.registry_reference or self.provenance_sha256)
        )


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
    fail_cause: Optional[Literal["sut", "test_artifact", "infrastructure"]] = None
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
    verification_level: Literal["twin", "hil", "physical"] = "twin"
    environment: ExecutionEnvironment = Field(default_factory=ExecutionEnvironment)
    submission_status: Optional[str] = None
    code_quality: Optional[CodeQuality] = None
    test_results: List[ExternalTestResult]
    package_manifest: Optional[Dict[str, Any]] = None
    package_verdict: Optional[Dict[str, Any]] = None
    package_metrics: Optional[Dict[str, Any]] = None
    model_config = {"json_schema_extra": {"examples": [{
        "schema_version": "1.0", "submission_id": "S-2026-11-18-0042", "run_id": "R-20261118-0197",
        "requirements_set_version": "2026-11-18", "code_sha256": "a" * 64, "contract_sha256": "b" * 64,
        "executed_at": "2026-11-18T12:00:00Z", "external_system": "IFARLAB",
        "environment": {"simulator": "Gazebo", "image": "ros2-exec-harness:0.3.2"},
        "test_results": [{"test_case_id": "MOTION_004", "status": "completed", "assertion_result": "PASS", "robot_verdict": "FAIL", "metrics": {"trajectory_duration": {"value": 23.4, "unit": "s"}, "collision_count": {"value": 0, "unit": "count"}}, "evidence": [{"evidence_id": "E-0197", "kind": "rosbag", "sha256": "c" * 64}], "validity": {"trustworthy": True}}],
    }]}}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
