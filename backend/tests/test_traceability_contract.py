from datetime import datetime, timezone

import pytest

from models.traceability import (
    CodeQuality, ExecutionEnvironment, GenerationProvenance, ManifestTest, RequirementSet,
    SubmissionManifest,
)
from services.traceability_contract import (
    canonical_json_bytes, contract_sha256, python_test_functions,
    format_submission_id, sha256_bytes, validate_manifest_mapping,
)


CODE = "def test_tc_001_motion():\n    assert True\n"


def manifest(**changes):
    code_hash = sha256_bytes(CODE.encode("utf-8"))
    values = dict(
        submission_id=format_submission_id("2026-11-18", 1),
        code_sha256=code_hash,
        requirements_set_version="2026-11-18",
        contract_sha256=contract_sha256(),
        generation=GenerationProvenance(provider=None, model=None, generated_at=datetime.now(timezone.utc)),
        code_quality=CodeQuality(),
        tests=[ManifestTest(function="test_tc_001_motion", test_case_id="TC_001", requirements=["FR-001"])],
    )
    values.update(changes)
    return SubmissionManifest(**values)


def test_complete_requirements_contract_preserves_unmeasurable_requirement():
    result = RequirementSet(requirements_set_version="v1", requirements=[{
        "id": "FR-001", "version": "1.0", "type": "functional", "text": "Move safely", "acceptance": []
    }])
    assert result.requirements[0].acceptance_review_required is True


def test_requirement_ids_are_unique():
    item = {"id": "FR-001", "version": "1", "type": "functional", "text": "x"}
    with pytest.raises(ValueError, match="unique"):
        RequirementSet(requirements_set_version="v1", requirements=[item, item])


def test_canonical_hash_is_order_independent():
    assert canonical_json_bytes({"b": 2, "a": 1}) == canonical_json_bytes({"a": 1, "b": 2})


def test_code_hash_uses_exact_utf8_bytes():
    assert sha256_bytes(CODE.encode("utf-8")) != sha256_bytes((CODE + "\n").encode("utf-8"))


def test_ast_function_mapping_accepts_exact_manifest():
    validate_manifest_mapping(CODE, manifest(), ["FR-001"], ["TC_001"])
    assert python_test_functions(CODE) == ["test_tc_001_motion"]


def test_ast_function_mapping_rejects_missing_function():
    with pytest.raises(ValueError, match="do not match"):
        validate_manifest_mapping(CODE, manifest(tests=[]), ["FR-001"], ["TC_001"])


def test_unknown_requirement_reference_is_rejected():
    with pytest.raises(ValueError, match="unknown requirement"):
        validate_manifest_mapping(CODE, manifest(), ["FR-002"], ["TC_001"])


def test_unknown_test_case_reference_is_rejected():
    with pytest.raises(ValueError, match="unknown test case"):
        validate_manifest_mapping(CODE, manifest(), ["FR-001"], ["TC_002"])


def test_missing_llm_metadata_is_not_fabricated():
    value = manifest()
    assert value.generation.provider is None
    assert value.generation.model is None
    assert value.code_quality.verdict == "not_recorded"


def test_incorrect_contract_hash_is_rejected():
    with pytest.raises(ValueError, match="contract_sha256"):
        validate_manifest_mapping(CODE, manifest(contract_sha256="0" * 64), ["FR-001"], ["TC_001"])


def test_unclassified_requirement_is_explicit_not_inferred():
    value = RequirementSet(requirements_set_version="v1", requirements=[{
        "id": "REQ-UNKNOWN", "version": "1", "type": "unclassified", "text": "Needs classification"
    }])
    assert value.requirements[0].type.value == "unclassified"


def test_digital_twin_environment_requires_provenance():
    incomplete = ExecutionEnvironment(scope="digital_twin", environment_id="env", digital_twin_id="dt")
    complete = ExecutionEnvironment(scope="digital_twin", environment_id="env", digital_twin_id="dt", registry_reference="registry://dt/1")
    assert incomplete.qualifies_as_digital_twin is False
    assert complete.qualifies_as_digital_twin is True
