import pytest

from mutation.evaluator import baseline_is_valid, calculate_score, classify_mutant


BASELINE = {"status": "completed", "tests": [{"test_id": "t1", "outcome": "passed"}, {"test_id": "t2", "outcome": "passed"}]}


@pytest.mark.parametrize("execution, expected", [
    ({"status": "completed", "tests": [{"test_id": "t1", "outcome": "failed"}, {"test_id": "t2", "outcome": "passed"}]}, "killed"),
    ({"status": "completed", "tests": [{"test_id": "t1", "outcome": "passed"}, {"test_id": "t2", "outcome": "passed"}]}, "survived"),
    ({"status": "invalid"}, "invalid"),
    ({"status": "timeout"}, "timeout"),
    ({"status": "execution_error"}, "execution_error"),
    ({"status": "completed", "tests": [], "equivalent_confirmed": True}, "equivalent"),
    ({"status": "completed", "tests": [{"test_id": "t1", "outcome": "passed"}]}, "undetermined"),
    ({"status": "not_executed"}, "not_executed"),
])
def test_classification(execution, expected):
    assert classify_mutant(BASELINE, execution) == expected


def test_failed_or_empty_baseline_is_never_used_for_mutation_verdicts():
    assert not baseline_is_valid({"status": "completed", "tests": []})
    assert classify_mutant({"status": "completed", "tests": [{"test_id": "t1", "outcome": "failed"}]}, {"status": "completed"}) == "undetermined"


def test_score_excludes_non_assessable_results_and_deduplicates():
    rows = [
        {"mutant_id": "m1", "outcome": "killed", "family": "AOR", "source_path": "a.py", "function": "f", "tests": [{"test_id": "t1", "outcome": "failed"}]},
        {"mutant_id": "m2", "outcome": "survived", "family": "AOR", "source_path": "a.py", "function": "f"},
        {"mutant_id": "m3", "outcome": "invalid", "family": "ROR", "source_path": "a.py"},
        {"mutant_id": "m1", "outcome": "killed", "family": "AOR", "source_path": "a.py", "function": "f", "tests": []},
    ]
    score = calculate_score(rows)
    assert score["unique_mutants"] == 3
    assert score["overall"] == {"killed": 1, "survived": 1, "denominator": 2, "score": .5, "assessable": True}
    assert calculate_score([{"mutant_id": "x", "outcome": "invalid"}])["overall"]["score"] is None

