from copy import deepcopy

from services.requirement_coverage_service import calculate_requirement_coverage


CODE_HASH = "a" * 64
PROVENANCE_HASH = "b" * 64


def requirement_set(requirements=None):
    return {
        "requirements_set_version": "demo-v1", "content_sha256": "c" * 64,
        "requirements": requirements if requirements is not None else [
            {"id": "FR-001", "version": "1", "type": "functional", "text": "Move", "status": "active", "applicable": True},
            {"id": "FR-002", "version": "1", "type": "functional", "text": "Stop", "status": "active", "applicable": True},
            {"id": "NFR-001", "version": "1", "type": "non_functional", "text": "Fast", "status": "active", "applicable": True},
            {"id": "NFR-002", "version": "1", "type": "non_functional", "text": "Safe", "status": "active", "applicable": True},
            {"id": "REQ-UNKNOWN", "version": "1", "type": "unclassified", "text": "Review", "status": "active", "applicable": True},
            {"id": "FR-OLD", "version": "1", "type": "functional", "text": "Old", "status": "superseded", "applicable": True},
        ],
    }


def submission(submission_id, tests, *, quality=True, version="demo-v1", project="demo"):
    return {
        "submission_id": submission_id, "code": "def test_example(): assert True",
        "manifest": {
            "submission_id": submission_id, "revision": 1, "requirements_set_version": version,
            "project_id": project, "session_id": "synthetic-session", "code_sha256": CODE_HASH,
            "code_quality": {"verdict": "pass" if quality else "fail", "syntax": "pass", "validator": "pass"},
            "tests": tests,
        },
    }


def mapping(case_id, requirements, scenario="TS-001", versions=None):
    return {"function": f"test_{case_id.lower()}_example", "test_case_id": case_id, "scenario_id": scenario, "requirements": requirements, "requirement_versions": versions or {}}


def delivery(submission_id, run_id, *, scope="digital_twin", linked=True, environment_id="DT-ENV-1"):
    return {
        "link_status": "linked" if linked else "rejected",
        "payload": {
            "submission_id": submission_id, "run_id": run_id, "requirements_set_version": "demo-v1",
            "environment": {"scope": scope, "environment_id": environment_id, "digital_twin_id": "DT-1", "provenance_sha256": PROVENANCE_HASH},
        },
    }


def verdict(submission_id, run_id, case_id, result="PASS", *, evidence=True, validity="VALID"):
    return {
        "verdict_id": f"V-{run_id}-{case_id}", "submission_id": submission_id, "run_id": run_id,
        "test_case_id": case_id, "final_verdict": result, "execution_validity": validity,
        "evidence": [{"evidence_id": "E-1", "kind": "log", "sha256": "d" * 64}] if evidence else [],
        "evaluated_at": "2026-11-19T10:00:00+00:00",
    }


def synthetic_evidence():
    submissions = [
        submission("S-FR1", [mapping("TC_001", ["FR-001"])]),
        submission("S-FR2", [mapping("TC_002", ["FR-002"])]),
        submission("S-NFR1", [mapping("TC_003", ["NFR-001"])]),
        submission("S-NFR2", [mapping("TC_004", ["NFR-002"])]),
        submission("S-UNKNOWN", [mapping("TC_005", ["REQ-UNKNOWN"])]),
    ]
    deliveries = [delivery("S-FR1", "R-1"), delivery("S-FR2", "R-2", scope="local"), delivery("S-NFR1", "R-3")]
    verdicts = [verdict("S-FR1", "R-1", "TC_001"), verdict("S-FR2", "R-2", "TC_002"), verdict("S-NFR1", "R-3", "TC_003", "FAIL")]
    return submissions, deliveries, verdicts


def test_synthetic_demo_separates_executed_and_verified_coverage():
    submissions, deliveries, verdicts = synthetic_evidence()
    result = calculate_requirement_coverage(requirement_set(), submissions, deliveries, verdicts)
    assert result["kpi"]["functional"]["percentage"] == 50.0
    assert result["verified"]["functional"]["percentage"] == 50.0
    assert result["kpi"]["non_functional"]["percentage"] == 50.0
    assert result["verified"]["non_functional"]["percentage"] == 0.0
    assert result["summary"]["unclassified_requirements"] == 1
    assert result["status"] == "assessed"


def test_non_dt_invalid_and_missing_evidence_do_not_count():
    case_mapping = mapping("TC_001", ["FR-001"])
    sub = submission("S-1", [case_mapping])
    for item_delivery, item_verdict in [
        (delivery("S-1", "R-1", scope="simulation"), verdict("S-1", "R-1", "TC_001")),
        (delivery("S-1", "R-1"), verdict("S-1", "R-1", "TC_001", evidence=False)),
        (delivery("S-1", "R-1", linked=False), verdict("S-1", "R-1", "TC_001")),
        (delivery("S-1", "R-1"), verdict("S-1", "R-1", "TC_001", validity="INVALID")),
        (delivery("S-1", "R-1"), verdict("S-1", "R-1", "TC_001", result="INCONCLUSIVE")),
    ]:
        result = calculate_requirement_coverage(requirement_set([requirement_set()["requirements"][0]]), [sub], [item_delivery], [item_verdict])
        assert result["kpi"]["functional"]["covered"] == 0


def test_duplicate_and_many_to_many_mappings_count_each_requirement_once():
    tests = [mapping("TC_001", ["FR-001", "NFR-001"]), mapping("TC_002", ["FR-001"])]
    sub = submission("S-1", tests)
    deliveries = [delivery("S-1", "R-1")]
    verdicts = [verdict("S-1", "R-1", "TC_001"), verdict("S-1", "R-1", "TC_002")]
    result = calculate_requirement_coverage(requirement_set(), [sub], deliveries, verdicts)
    assert result["kpi"]["functional"]["covered"] == 1
    assert result["kpi"]["non_functional"]["covered"] == 1


def test_contradictory_valid_verdicts_execute_but_do_not_verify():
    sub = submission("S-1", [mapping("TC_001", ["FR-001"]), mapping("TC_002", ["FR-001"])])
    deliveries = [delivery("S-1", "R-1")]
    verdicts = [verdict("S-1", "R-1", "TC_001", "PASS"), verdict("S-1", "R-1", "TC_002", "FAIL")]
    result = calculate_requirement_coverage(requirement_set([requirement_set()["requirements"][0]]), [sub], deliveries, verdicts)
    assert result["kpi"]["functional"]["percentage"] == 100.0
    assert result["verified"]["functional"]["percentage"] == 0.0
    assert result["requirements"][0]["verification_state"] == "FAIL"


def test_missing_scenario_and_stale_version_break_the_valid_chain():
    missing = submission("S-1", [mapping("TC_001", ["FR-001"], scenario=None)])
    stale = submission("S-2", [mapping("TC_002", ["FR-001"], versions={"FR-001": "0"})])
    result = calculate_requirement_coverage(requirement_set([requirement_set()["requirements"][0]]), [missing, stale], [], [])
    row = result["requirements"][0]
    assert row["mapped"] is False
    assert row["executed_dt"] is False
    assert any(chain["stale"] for chain in row["traceability_chains"])


def test_empty_or_unclassified_only_sets_are_not_assessable():
    empty = calculate_requirement_coverage(requirement_set([]), [], [], [])
    assert empty["kpi"]["functional"]["percentage"] is None
    assert empty["kpi"]["functional"]["assessment"] == "not_assessable"
    unclassified = calculate_requirement_coverage(requirement_set([requirement_set()["requirements"][4]]), [], [], [])
    assert unclassified["status"] == "not_assessable"


def test_project_and_environment_filters_are_deterministic():
    submissions, deliveries, verdicts = synthetic_evidence()
    wrong_project = calculate_requirement_coverage(requirement_set(), submissions, deliveries, verdicts, project_id="other")
    assert wrong_project["kpi"]["functional"]["covered"] == 0
    wrong_environment = calculate_requirement_coverage(requirement_set(), submissions, deliveries, verdicts, environment_id="DT-OTHER")
    assert wrong_environment["kpi"]["functional"]["covered"] == 0


def test_superseded_requirement_is_preserved_but_excluded_from_denominator():
    result = calculate_requirement_coverage(requirement_set(), [], [], [])
    assert result["kpi"]["functional"]["total_applicable"] == 2
    assert all(row["id"] != "FR-OLD" for row in result["requirements"])


def test_native_requirement_parser_uses_only_explicit_identifiers():
    from services.requirement_analysis_service import RequirementAnalysisService
    parsed = RequirementAnalysisService._structured_requirements(
        "FR1. Move the robot\nNFR2. Complete within 20 seconds\nThis prose has no stable identifier",
        "requirements.txt",
    )
    assert [item.id for item in parsed.requirements] == ["FR-001", "NFR-002"]
    assert [item.type.value for item in parsed.requirements] == ["functional", "non_functional"]
    assert parsed.requirements[0].source_artifact_sha256


