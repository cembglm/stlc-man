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
        matches = [row for row in self.rows if all(row.get(k) == v for k, v in query.items())]
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
        manifest = {"submission_id": "S-2026-11-18-0001", "revision": 1, "code_sha256": "a" * 64, "contract_sha256": contract_sha256(), "requirements_set_version": "v1", "generation": {"model": "m"}, "code_quality": {"verdict": "pass"}, "tests": [{"function": "test_tc_001_motion", "test_case_id": "TC_001", "requirements": ["NFR-001"], "oracle": {}}]}
        self.traceability_submissions = FakeCollection([{"submission_id": "S-2026-11-18-0001", "revision": 1, "manifest": manifest, "code": "def test_tc_001_motion(): pass"}])
        self.ifarlab_result_deliveries = FakeCollection()
        self.verification_verdicts = FakeCollection()
        self.traceability_events = FakeCollection()


def payload(**changes):
    value = dict(
        schema_version="1.0", submission_id="S-2026-11-18-0001", run_id="R-20261118-0001", requirements_set_version="v1",
        code_sha256="a" * 64, contract_sha256=contract_sha256(), executed_at=datetime.now(timezone.utc),
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


def test_external_authentication_rejects_invalid_key(monkeypatch):
    monkeypatch.setattr(auth, "get_settings", lambda: SimpleNamespace(api_auth_enabled=True, app_api_key="secret"))
    with pytest.raises(HTTPException) as exc:
        run(auth.require_api_key(header_key="wrong", bearer=None))
    assert exc.value.status_code == 401
