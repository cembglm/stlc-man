import pytest

from services.execution_client import ExecutionRequest, SshDockerExecutionClient


def test_contract_filename_is_used_when_submission_metadata_exists():
    request = ExecutionRequest(
        test_code="def test_insp_004_scratch(): pass",
        test_case_id="INSP_004",
        metadata={"submission_id": "S-2026-11-21-0003", "short_name": "Scratch 2mm"},
    )
    assert SshDockerExecutionClient._submission_filename(request, "exec-old") == (
        "S-2026-11-21-0003__INSP_004__scratch_2mm.py"
    )


def test_legacy_filename_remains_for_transition_callers():
    request = ExecutionRequest(test_code="def test_example(): pass")
    assert SshDockerExecutionClient._submission_filename(request, "exec-abc") == "exec-abc.py"


def test_partial_traceability_metadata_is_rejected():
    request = ExecutionRequest(test_code="def test_example(): pass", test_case_id="INSP_004")
    with pytest.raises(ValueError, match="submission_id"):
        SshDockerExecutionClient._submission_filename(request, "exec-abc")
