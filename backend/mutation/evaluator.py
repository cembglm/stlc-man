"""Deterministic mutation classification and score calculation."""

from collections import defaultdict
from typing import Dict, Iterable, Optional

from .models import MutationOutcome


def baseline_is_valid(baseline: Dict) -> bool:
    return baseline.get("status") == "completed" and all(
        test.get("outcome") == "passed" for test in baseline.get("tests", [])
    ) and bool(baseline.get("tests"))


def classify_mutant(baseline: Dict, execution: Optional[Dict]) -> str:
    if not baseline_is_valid(baseline):
        return MutationOutcome.UNDETERMINED.value
    if not execution or execution.get("status") in {None, "not_executed"}:
        return MutationOutcome.NOT_EXECUTED.value
    status = execution.get("status")
    if status == "invalid":
        return MutationOutcome.INVALID.value
    if status == "timeout":
        return MutationOutcome.TIMEOUT.value
    if status == "execution_error":
        return MutationOutcome.EXECUTION_ERROR.value
    if status != "completed":
        return MutationOutcome.UNDETERMINED.value
    if execution.get("equivalent_confirmed") is True:
        return MutationOutcome.EQUIVALENT.value
    base = {t.get("test_id"): t.get("outcome") for t in baseline.get("tests", [])}
    observed = {t.get("test_id"): t.get("outcome") for t in execution.get("tests", [])}
    if not observed or any(test_id not in observed for test_id in base):
        return MutationOutcome.UNDETERMINED.value
    if any(outcome == "passed" and observed.get(test_id) == "failed" for test_id, outcome in base.items()):
        return MutationOutcome.KILLED.value
    if all(observed.get(test_id) == outcome for test_id, outcome in base.items()):
        return MutationOutcome.SURVIVED.value
    return MutationOutcome.UNDETERMINED.value


def calculate_score(results: Iterable[Dict]) -> Dict:
    unique = {item["mutant_id"]: item for item in results}
    counts = defaultdict(int)
    groups = {"family": defaultdict(lambda: defaultdict(int)), "file": defaultdict(lambda: defaultdict(int)),
              "function": defaultdict(lambda: defaultdict(int))}
    detecting_tests = defaultdict(list)
    for item in unique.values():
        outcome = item.get("outcome", MutationOutcome.UNDETERMINED.value)
        counts[outcome] += 1
        for dimension, field in (("family", "family"), ("file", "source_path"), ("function", "function")):
            groups[dimension][item.get(field) or "<module>"][outcome] += 1
        if outcome == MutationOutcome.KILLED.value:
            for test in item.get("tests", []):
                if test.get("outcome") == "failed":
                    detecting_tests[test.get("test_id", "unknown")].append(item["mutant_id"])
    def summary(values):
        killed, survived = values.get("killed", 0), values.get("survived", 0)
        denominator = killed + survived
        return {"killed": killed, "survived": survived, "denominator": denominator,
                "score": (killed / denominator) if denominator else None,
                "assessable": bool(denominator)}
    return {"overall": summary(counts), "counts": dict(counts),
            "breakdown": {dim: {key: summary(vals) for key, vals in value.items()} for dim, value in groups.items()},
            "detecting_tests": dict(detecting_tests), "unique_mutants": len(unique)}
