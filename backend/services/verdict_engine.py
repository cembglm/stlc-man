"""Deterministic, LLM-free verification engine."""

from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Iterable, List, Optional, Tuple


ENGINE_VERSION = "1.0.0"
RULE_SET_VERSION = "1.0"
SUPPORTED_OPERATORS = {"==", "!=", "<", "<=", ">", ">=", "in", "not_in"}
UNIT_ALIASES = {"sec": "s", "second": "s", "seconds": "s", "radian": "rad", "radians": "rad"}


def _unit(value: Optional[str]) -> Optional[str]:
    if not value:
        return None
    normalized = value.strip().lower()
    return UNIT_ALIASES.get(normalized, normalized)


def _decimal(value: Any) -> Decimal:
    if isinstance(value, bool):
        raise InvalidOperation("boolean is not numeric")
    return Decimal(str(value))


def compare(actual: Any, operator: str, threshold: Any, actual_unit=None, rule_unit=None) -> bool:
    if operator not in SUPPORTED_OPERATORS:
        raise ValueError(f"unsupported operator: {operator}")
    if _unit(actual_unit) != _unit(rule_unit):
        raise ValueError(f"incompatible units: {actual_unit!r} and {rule_unit!r}")
    if operator in {"in", "not_in"}:
        if not isinstance(threshold, (list, tuple, set)):
            raise ValueError(f"{operator} requires a list threshold")
        outcome = actual in threshold
        return outcome if operator == "in" else not outcome
    try:
        left, right = _decimal(actual), _decimal(threshold)
    except (InvalidOperation, ValueError):
        left, right = actual, threshold
    return {
        "==": lambda: left == right, "!=": lambda: left != right,
        "<": lambda: left < right, "<=": lambda: left <= right,
        ">": lambda: left > right, ">=": lambda: left >= right,
    }[operator]()


def evaluate_test(
    *, rules: Iterable[Dict[str, Any]], metrics: Dict[str, Dict[str, Any]],
    assertion_result: Optional[str], robot_verdict: Optional[str],
    evidence: List[Dict[str, Any]], validity: Dict[str, Any],
    code_quality_verdict: Optional[str] = None,
) -> Dict[str, Any]:
    issues = []
    # A reset failure is a binding FAIL (Decision 14), not invalid evidence.
    # A twin crash during the test remains INCONCLUSIVE.
    for key in ("infrastructure_failed", "timed_out", "environment_invalid", "skipped", "blocked", "not_executed", "trustworthy"):
        value = validity.get(key)
        if value is True and key != "trustworthy": issues.append(key)
        if key == "trustworthy" and value is False: issues.append("execution_not_trustworthy")
    if not evidence:
        issues.append("required_evidence_unavailable")
    if validity.get("exit_code") in {3, 64}:
        issues.append(f"execution_not_started_exit_{validity['exit_code']}")
    rtf = metrics.get("rtf_min")
    if rtf and rtf.get("status", "measured") == "measured":
        try:
            if _decimal(rtf.get("value")) < Decimal("0.7"):
                issues.append("rtf_below_0.7")
        except (InvalidOperation, ValueError, TypeError):
            issues.append("invalid_measurement:rtf_min")

    outcomes = []
    for rule in rules:
        metric_name = rule["metric"]
        measurement = metrics.get(metric_name)
        if measurement is None or measurement.get("status", "measured") == "unavailable":
            outcomes.append({**rule, "passed": None, "reason": "measurement_unavailable"})
            issues.append(f"missing_measurement:{metric_name}")
            continue
        try:
            passed = compare(
                measurement.get("value"), rule["operator"], rule["threshold"],
                measurement.get("unit"), rule.get("unit"),
            )
            outcomes.append({**rule, "actual": measurement.get("value"), "passed": passed})
        except ValueError as exc:
            outcomes.append({**rule, "actual": measurement.get("value"), "passed": None, "reason": str(exc)})
            issues.append(f"invalid_measurement:{metric_name}")

    assertion = (assertion_result or "").upper()
    robot = (robot_verdict or "").upper()
    contradiction = assertion in {"PASS", "FAIL"} and robot in {"PASS", "FAIL"} and assertion != robot
    reset_status = (metrics.get("reset_status") or {}).get("value")
    reset_failed = validity.get("reset_failed") is True or reset_status in {"failed", "stack_down", "timeout"}
    if issues or any(item["passed"] is None for item in outcomes):
        final = "INCONCLUSIVE"
    elif reset_failed or (code_quality_verdict or "").lower() == "fail" or any(item["passed"] is False for item in outcomes) or assertion == "FAIL" or robot == "FAIL":
        final = "FAIL"
    elif outcomes and all(item["passed"] is True for item in outcomes) and assertion == "PASS" and robot == "PASS":
        final = "PASS"
    else:
        final = "INCONCLUSIVE"
        issues.append("insufficient_verdict_inputs")
    failed = [item["metric"] for item in outcomes if item["passed"] is False]
    explanation = (
        "Failed rules: " + ", ".join(failed) if failed else
        "Execution is inconclusive: " + ", ".join(sorted(set(issues))) if final == "INCONCLUSIVE" else
        "All applicable deterministic rules, generated assertions, and independent robot checks passed."
    )
    fail_cause = None
    if final == "FAIL":
        if (code_quality_verdict or "").lower() == "fail":
            fail_cause = "test_artifact"
        elif reset_status in {"stack_down", "timeout"}:
            fail_cause = "infrastructure"
        else:
            fail_cause = "sut"
    return {
        "verdict_engine_version": ENGINE_VERSION,
        "rule_set_version": RULE_SET_VERSION,
        "execution_validity": "INVALID" if issues else "VALID",
        "assertion_result": assertion_result,
        "independent_robot_evaluation": robot_verdict,
        "code_quality_verdict": code_quality_verdict or "not_recorded",
        "contradiction": contradiction,
        "applied_rules": outcomes,
        "final_verdict": final,
        "fail_cause": fail_cause,
        "issues": sorted(set(issues)),
        "explanation": explanation,
    }


def aggregate_requirement(test_verdicts: Iterable[str], covered: bool, stale: bool = False) -> str:
    values = [value.upper() for value in test_verdicts]
    if stale: return "STALE"
    if not covered: return "NOT_COVERED"
    if "FAIL" in values: return "FAIL"
    if values and all(value == "PASS" for value in values): return "PASS"
    return "NOT_VERIFIED"
