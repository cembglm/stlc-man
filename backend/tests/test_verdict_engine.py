import copy

import pytest

from services.verdict_engine import ENGINE_VERSION, aggregate_requirement, compare, evaluate_test


def evidence():
    return [{"evidence_id": "E-1", "kind": "rosbag", "sha256": "a" * 64}]


def evaluate(rules, metrics, **changes):
    args = dict(rules=rules, metrics=metrics, assertion_result="PASS", robot_verdict="PASS", evidence=evidence(), validity={"trustworthy": True})
    args.update(changes)
    return evaluate_test(**args)


@pytest.mark.parametrize("operator,actual,threshold,expected", [
    ("<=", 20, 20, True), ("<=", 20.0001, 20, False), (">=", "0.10", "0.1", True), ("!=", 2, 1, True)
])
def test_boundary_comparisons(operator, actual, threshold, expected):
    assert compare(actual, operator, threshold, "s", "s") is expected


def test_incompatible_units_are_rejected():
    with pytest.raises(ValueError, match="incompatible units"):
        compare(1, "<=", 2, "rad", "s")


def test_missing_measurement_is_inconclusive():
    result = evaluate([{"metric": "duration", "operator": "<=", "threshold": 20, "unit": "s"}], {})
    assert result["final_verdict"] == "INCONCLUSIVE"


def test_missing_evidence_cannot_pass():
    result = evaluate([], {}, evidence=[])
    assert result["final_verdict"] == "INCONCLUSIVE"


def test_collision_detection_fails():
    result = evaluate([{"metric": "collision_count", "operator": "==", "threshold": 0, "unit": "count"}], {"collision_count": {"value": 1, "unit": "count"}})
    assert result["final_verdict"] == "FAIL"


def test_joint_limit_violation_fails():
    result = evaluate([{"metric": "joint_limit_violations", "operator": "==", "threshold": 0, "unit": "count"}], {"joint_limit_violations": {"value": 1, "unit": "count"}})
    assert result["final_verdict"] == "FAIL"


def test_successful_expected_rejection_passes():
    rules = [{"metric": "rejected", "operator": "==", "threshold": True, "unit": None}, {"metric": "rejection_reason", "operator": "==", "threshold": "joint_limit", "unit": None}]
    metrics = {"rejected": {"value": True}, "rejection_reason": {"value": "joint_limit"}}
    assert evaluate(rules, metrics)["final_verdict"] == "PASS"


def test_incorrect_rejection_reason_fails():
    rule = {"metric": "rejection_reason", "operator": "==", "threshold": "joint_limit", "unit": None}
    assert evaluate([rule], {"rejection_reason": {"value": "timeout"}})["final_verdict"] == "FAIL"


@pytest.mark.parametrize("validity,issue", [({"timed_out": True}, "timed_out"), ({"reset_failed": True}, "reset_failed")])
def test_invalid_execution_is_inconclusive(validity, issue):
    result = evaluate([], {}, validity=validity)
    assert result["final_verdict"] == "INCONCLUSIVE"
    assert issue in result["issues"]


def test_assertion_robot_disagreement_is_recorded_and_fails():
    result = evaluate([], {}, assertion_result="PASS", robot_verdict="FAIL")
    assert result["contradiction"] is True
    assert result["final_verdict"] == "FAIL"


def test_code_quality_failure_cannot_become_pass():
    result = evaluate([], {}, code_quality_verdict="fail")
    assert result["final_verdict"] == "FAIL"
    assert result["code_quality_verdict"] == "fail"


def test_rtf_below_design_threshold_is_inconclusive():
    result = evaluate([], {"rtf_min": {"value": 0.69, "unit": "ratio"}})
    assert result["final_verdict"] == "INCONCLUSIVE"
    assert "rtf_below_0.7" in result["issues"]


def test_design_acceptance_vector_duration_23_4_fails():
    rules = [
        {"requirement_id": "NFR-001", "metric": "trajectory_duration_s", "operator": "<=", "threshold": 20, "unit": "s"},
        {"source": "oracle", "metric": "final_joint_error_rad", "operator": "<=", "threshold": 0.01, "unit": "rad"},
        {"source": "general", "metric": "collision_count", "operator": "==", "threshold": 0, "unit": "count"},
    ]
    metrics = {
        "trajectory_duration_s": {"value": 23.4, "unit": "s"},
        "final_joint_error_rad": {"value": 0.001, "unit": "rad"},
        "collision_count": {"value": 0, "unit": "count"},
    }
    result = evaluate(rules, metrics, assertion_result="PASS", robot_verdict="FAIL")
    assert result["final_verdict"] == "FAIL"
    assert result["contradiction"] is True


def test_requirement_aggregation_precedence():
    assert aggregate_requirement([], covered=False) == "NOT_COVERED"
    assert aggregate_requirement(["PASS", "INCONCLUSIVE"], covered=True) == "NOT_VERIFIED"
    assert aggregate_requirement(["PASS", "FAIL"], covered=True) == "FAIL"
    assert aggregate_requirement(["PASS"], covered=True, stale=True) == "STALE"


def test_identical_inputs_are_deterministic():
    args = dict(rules=[{"metric": "x", "operator": "<=", "threshold": 1, "unit": "s"}], metrics={"x": {"value": 1, "unit": "s"}})
    assert evaluate(**copy.deepcopy(args)) == evaluate(**copy.deepcopy(args))
    assert evaluate(**args)["verdict_engine_version"] == ENGINE_VERSION
