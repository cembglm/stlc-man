from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


class MutationOutcome(str, Enum):
    KILLED = "killed"
    SURVIVED = "survived"
    INVALID = "invalid"
    TIMEOUT = "timeout"
    EXECUTION_ERROR = "execution_error"
    EQUIVALENT = "equivalent"
    UNDETERMINED = "undetermined"
    NOT_EXECUTED = "not_executed"


class CampaignStatus(str, Enum):
    DRAFT = "draft"
    GENERATED = "generated"
    BASELINE_UNAVAILABLE = "baseline_unavailable"
    READY = "ready"
    RUNNING = "running"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class CampaignCreate(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    source: str = Field(min_length=1, max_length=1_000_000)
    source_path: str = Field(default="module.py", min_length=1, max_length=500)
    language: str = "python"
    operator_families: List[str] = Field(default_factory=lambda: ["AOR", "ROR", "LOR", "CON"])
    max_mutants: Optional[int] = Field(default=None, ge=1, le=5000)
    seed: Optional[int] = None
    function_scope: Optional[str] = Field(default=None, max_length=300)
    requirement_refs: List[str] = Field(default_factory=list)
    test_refs: List[str] = Field(default_factory=list)
    project_id: Optional[str] = Field(default=None, max_length=200)
    source_artifact_id: Optional[str] = Field(default=None, max_length=300)
    source_version: Optional[str] = Field(default=None, max_length=200)
    test_suite_hash: Optional[str] = Field(default=None, max_length=128)
    execution_configuration: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("language")
    def supported_language_name(cls, value):
        if value not in {"python", "cpp_ros2"}:
            raise ValueError("language must be python or cpp_ros2")
        return value

    @field_validator("operator_families")
    def supported_operators(cls, value):
        normalized = list(dict.fromkeys(item.upper() for item in value))
        unknown = set(normalized) - {"AOR", "ROR", "LOR", "CON"}
        if unknown:
            raise ValueError(f"unsupported operator families: {sorted(unknown)}")
        if not normalized:
            raise ValueError("at least one operator family is required")
        return normalized


class ResultEvidence(BaseModel):
    mutant_id: str
    status: str = "completed"
    tests: List[Dict[str, Any]] = Field(default_factory=list)
    error: Optional[str] = None
    equivalent_confirmed: bool = False
    evidence_ref: Optional[str] = None


class BaselineEvidence(BaseModel):
    status: str
    tests: List[Dict[str, Any]] = Field(default_factory=list)
    evidence_ref: Optional[str] = None


class CampaignConfigurationUpdate(BaseModel):
    operator_families: Optional[List[str]] = None
    max_mutants: Optional[int] = Field(default=None, ge=1, le=5000)
    seed: Optional[int] = None
    function_scope: Optional[str] = Field(default=None, max_length=300)

    @field_validator("operator_families")
    def supported_operators(cls, value):
        if value is None:
            return value
        normalized = list(dict.fromkeys(item.upper() for item in value))
        if not normalized or set(normalized) - {"AOR", "ROR", "LOR", "CON"}:
            raise ValueError("operator_families must contain only AOR, ROR, LOR, CON")
        return normalized

