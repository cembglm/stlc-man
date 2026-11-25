from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from fastapi import HTTPException

import core.auth as auth
from models.traceability import IFARLABResult
from services.traceability_contract import contract_sha256
from services.traceability_service import TraceabilityService


class InsertResult:
    inserted_id = "fake"


class FakeCursor:
    def __init__(self, rows): self.rows = rows
    def __aiter__(self): self.iterator = iter(self.rows); return self
    async def __anext__(self):
        try: return next(self.iterator)
        except StopIteration: raise StopAsyncIteration


class FakeCollection:
    def __init__(self, rows=None): self.rows = list(rows or [])
    async def find_one(self, query, **kwargs):
        def nested(row, key):
            value = row
            for part in key.split("."):
                value = value.get(part) if isinstance(value, dict) else None
            return value
        matches = [row for row in self.rows if all(nested(row, k) == v for k, v in query.items())]
        return matches[-1] if matches else None
    async def insert_one(self, value): self.rows.append(dict(value)); return InsertResult()
    async def insert_many(self, values): self.rows.extend(dict(value) for value in values); return InsertResult()
    async def update_many(self, query, update):
        for row in self.rows:
            if all(row.get(k) == v for k, v in query.items()): row.update(update.get("$set", {}))
    def find(self, query): return FakeCursor([row for row in self.rows if all(row.get(k) == v for k, v in query.items())])


class FakeDB:
    def __init__(self):
        self.requirement_sets = FakeCollection([{"requirements_set_version": "v1", "is_current": True, "requirements": [{"id": "NFR-001", "version": "1", "type": "non_functional", "text": "Fast", "acceptance": [{"metric": "trajectory_duration_s", "operator": "<=", "threshold": 20, "unit": "s"}]}]}])
        manifest = {"submission_id": "S-2026-11-18-0001", "revision": 1, "code_sha256": "a" * 64, "contract_sha256": contract_sha256(), "requirements_set_version": "v1", "generation": {"model": "m"}, "code_quality": {"validator": "pass", "syntax": "pass", "verdict": "pass"}, "tests": [{"function": "test_tc_001_motion", "test_case_id": "TC_001", "scenario_id": "TS-001", "requirements": ["NFR-001"], "oracle": {}}]}
        self.traceability_submissions = FakeCollection([{"submission_id": "S-2026-11-18-0001", "revision": 1, "manifest": manifest, "code": "def test_tc_001_motion(): pass"}])
        self.ifarlab_result_deliveries = FakeCollection()
        self.verification_verdicts = FakeCollection()
        self.traceability_events = FakeCollection()
        self.defects = FakeCollection()
        self.test_regeneration_queue = FakeCollection()
        self.infrastructure_notifications = FakeCollection()
        self.review_queue = FakeCollection()


def payload(**changes):
    value = dict(
        schema_version="1.0", submission_id="S-2026-11-18-0001", run_id="R-20261118-0001", requirements_set_version="v1",
        code_sha256="a" * 64, contract_sha256=contract_sha256(), executed_at=datetime.now(timezone.utc),
        environment={"scope": "digital_twin", "environment_id": "DT-ENV-1", "digital_twin_id": "DT-1", "provenance_sha256": "d" * 64},
        test_results=[{"test_case_id": "TC_001", "status": "completed", "assertion_result": "PASS", "robot_verdict": "PASS", "external_verdict": "PASS", "metrics": {
            "trajectory_duration_s": {"value": 19, "unit": "s"}, "collision_count": {"value": 0, "unit": "count"},
            "joint_limit_violation_count": {"value": 0, "unit": "count"}, "velocity_limit_violation_count": {"value": 0, "unit": "count"},
            "acceleration_limit_violation_count": {"value": 0, "unit": "count"}, "scene_clean": {"value": True}, "reset_status": {"value": "success"}, "rtf_min": {"value": 0.9, "unit": "ratio"},
        }, "evidence": [{"evidence_id": "E-1", "kind": "rosbag", "sha256": "c" * 64}], "validity": {"trustworthy": True}}],
    )
    value.update(changes)
    return IFARLABResult(**value)


def service_with(db):
    service = TraceabilityService()
    async def get_db(): return db
    service._db = get_db
    return service


def run(coroutine):
    """Drive fake-I/O coroutines without a Windows event-loop socketpair."""
    try:
        coroutine.send(None)
    except StopIteration as completed:
        return completed.value
    raise AssertionError("fake coroutine unexpectedly yielded")


def test_result_ingestion_and_idempotent_replay():
    db, service = FakeDB(), None
    service = service_with(db)
    delivery = payload()
    first = run(service.ingest_result(delivery))
    second = run(service.ingest_result(delivery))
    assert first["link_status"] == "linked"
    assert first["evaluations"][0]["final_verdict"] == "PASS"
    assert second["idempotent_replay"] is True
    assert len(db.ifarlab_result_deliveries.rows) == 1


def test_hash_mismatch_is_stored_as_rejected():
    db = FakeDB()
    result = run(service_with(db).ingest_result(payload(code_sha256="b" * 64)))
    assert result["link_status"] == "rejected"
    assert "code_hash_mismatch" in result["rejection_reasons"]
    assert len(db.ifarlab_result_deliveries.rows) == 1


def test_unknown_submission_is_preserved_unlinked():
    db = FakeDB()
    result = run(service_with(db).ingest_result(payload(submission_id="S-2026-11-18-9999")))
    assert result["link_status"] == "unlinked"
    assert result["evaluations"][0]["final_verdict"] == "INCONCLUSIVE"


def test_corrected_delivery_does_not_overwrite_original():
    db, service = FakeDB(), None
    service = service_with(db)
    run(service.ingest_result(payload()))
    run(service.ingest_result(payload(run_id="R-20261118-0002")))
    assert len(db.ifarlab_result_deliveries.rows) == 2
    assert {row["payload"]["run_id"] for row in db.ifarlab_result_deliveries.rows} == {"R-20261118-0001", "R-20261118-0002"}


def test_same_run_id_with_different_content_is_rejected():
    db, service = FakeDB(), None
    service = service_with(db)
    run(service.ingest_result(payload()))
    changed = payload(test_results=[{
        **payload().test_results[0].model_dump(mode="json"),
        "metrics": {**payload().test_results[0].model_dump(mode="json")["metrics"], "trajectory_duration_s": {"value": 18, "unit": "s"}},
    }])
    with pytest.raises(ValueError, match="run_id already exists"):
        run(service.ingest_result(changed))
    assert len(db.ifarlab_result_deliveries.rows) == 1


def test_external_authentication_rejects_invalid_key(monkeypatch):
    monkeypatch.setattr(auth, "get_settings", lambda: SimpleNamespace(api_auth_enabled=True, app_api_key="secret"))
    with pytest.raises(HTTPException) as exc:
        run(auth.require_api_key(header_key="wrong", bearer=None))
    assert exc.value.status_code == 401


def test_end_to_end_ingestion_to_kpi_report():
    from services.requirement_coverage_service import RequirementCoverageService
    db = FakeDB()
    service = service_with(db)
    run(service.ingest_result(payload()))
    report = run(RequirementCoverageService(service).calculate(requirements_set_version="v1"))
    assert report["kpi"]["non_functional"]["percentage"] == 100.0
    assert report["verified"]["non_functional"]["percentage"] == 100.0
    assert report["requirements"][0]["traceability_chains"][0]["executions"][0]["dt_eligible"] is True


def test_non_sut_failure_is_preserved_as_not_verified():
    db = FakeDB()
    service = service_with(db)
    failed = payload(test_results=[{
        **payload().test_results[0].model_dump(mode="json"),
        "assertion_result": "FAIL", "robot_verdict": "FAIL", "external_verdict": "FAIL",
        "fail_cause": "test_artifact",
    }])
    run(service.ingest_result(failed))
    dashboard = run(service.dashboard())
    assert dashboard["requirements"][0]["verification_state"] == "NOT_VERIFIED"
    assert db.verification_verdicts.rows[0]["fail_cause"] == "test_artifact"
    assert len(db.defects.rows) == 0
    assert len(db.test_regeneration_queue.rows) == 1


def test_sut_failure_opens_one_defect_and_disagreement_opens_review():
    db = FakeDB()
    failed = payload(test_results=[{
        **payload().test_results[0].model_dump(mode="json"),
        "assertion_result": "PASS", "robot_verdict": "PASS",
        "external_verdict": "FAIL", "fail_cause": "sut",
    }])
    service = service_with(db)
    run(service.ingest_result(failed))
    replay = run(service.ingest_result(failed))
    assert replay["idempotent_replay"] is True
    assert len(db.defects.rows) == 1
    assert len(db.review_queue.rows) == 1
    assert db.review_queue.rows[0]["binding_source"] == "IFARLAB"


def test_regression_run_records_pass_to_fail_comparison():
    db = FakeDB()
    source = db.traceability_submissions.rows[0]
    candidate_manifest = {
        **source["manifest"], "submission_id": "S-2026-11-18-0002",
    }
    db.traceability_submissions.rows.append({
        "submission_id": "S-2026-11-18-0002", "revision": 1,
        "manifest": candidate_manifest, "code": source["code"],
        "regression_source_submission_id": "S-2026-11-18-0001",
        "regression_campaign_id": "REG-1",
    })
    db.verification_verdicts.rows.append({
        "verdict_id": "V-baseline", "submission_id": "S-2026-11-18-0001",
        "test_case_id": "TC_001", "final_verdict": "PASS", "authoritative_verdict": "PASS",
    })
    db.regression_comparisons = FakeCollection()
    failed = payload(
        submission_id="S-2026-11-18-0002", run_id="R-20261118-0002",
        test_results=[{
            **payload().test_results[0].model_dump(mode="json"),
            "assertion_result": "FAIL", "robot_verdict": "FAIL",
            "external_verdict": "FAIL", "fail_cause": "sut",
        }],
    )
    result = run(service_with(db).ingest_result(failed))
    assert result["regression_comparison"]["regression_count"] == 1
    assert db.regression_comparisons.rows[0]["rows"][0]["classification"] == "regression"
