from datetime import datetime, timezone

import pytest

from models.ifarlab_lifecycle import RCBuildRequest, ReviewDecision
from services.lifecycle_service import build_rc_report, resolve_review


class Collection:
    def __init__(self, rows=None):
        self.rows = list(rows or [])

    async def find_one(self, query):
        return next((row for row in self.rows if all(row.get(k) == v for k, v in query.items())), None)

    async def insert_one(self, record):
        self.rows.append(dict(record))

    def find(self, query):
        rows = [row for row in self.rows if all(row.get(k) == v for k, v in query.items())]
        class Cursor:
            def __aiter__(self): self.iterator = iter(rows); return self
            async def __anext__(self):
                try: return next(self.iterator)
                except StopIteration: raise StopAsyncIteration
        return Cursor()


class DB:
    def __init__(self):
        self.review_queue = Collection([{
            "review_id": "REV-abc123", "run_id": "R-20261125-0001", "test_case_id": "REF_001",
        }])
        self.verification_verdicts = Collection([{
            "verdict_id": "V-1", "run_id": "R-20261125-0001", "test_case_id": "REF_001",
            "final_verdict": "FAIL", "authoritative_verdict": "FAIL",
        }])
        self.review_decisions = Collection()


class RCDB:
    def __init__(self):
        self.requirement_sets = Collection([{
            "requirements_set_version": "QCR-2026-11-25",
            "requirements": [{"id": "QCR-001", "priority": "mandatory"}],
        }])
        self.verification_verdicts = Collection([{
            "requirement_ids": ["QCR-001"], "final_verdict": "PASS",
            "environment": {"sut_version": "1.2.0"},
        }])
        self.defects = Collection()
        self.regression_comparisons = Collection()
        self.mutant_requests = Collection()
        self.mutant_results = Collection()
        self.rc_reports = Collection()


def drive(coroutine):
    try:
        coroutine.send(None)
    except StopIteration as complete:
        return complete.value
    raise AssertionError("unexpected async yield")


def test_review_resolution_is_append_only_and_creates_superseding_verdict():
    db = DB()
    result = drive(resolve_review(db, ReviewDecision(
        review_id="REV-abc123", decision_id="RVD-abc123", reviewer="ASRLab reviewer",
        decided_at=datetime.now(timezone.utc), decision="accept_asrlab",
        authoritative_verdict="PASS", rationale="Evidence review completed.",
        supersedes_verdict_id="V-1",
    )))
    assert result["superseding_verdict"]["supersedes_verdict_id"] == "V-1"
    assert db.verification_verdicts.rows[0]["final_verdict"] == "FAIL"
    assert db.verification_verdicts.rows[1]["final_verdict"] == "PASS"
    with pytest.raises(ValueError, match="already exists"):
        drive(resolve_review(db, ReviewDecision(
            review_id="REV-abc123", decision_id="RVD-again", reviewer="other",
            decided_at=datetime.now(timezone.utc), decision="inconclusive",
            authoritative_verdict="INCONCLUSIVE", rationale="duplicate",
            supersedes_verdict_id="V-1",
        )))


def test_rc_is_derived_from_snapshot_and_stays_ineligible_without_mutation_evidence():
    db = RCDB()
    report = drive(build_rc_report(db, RCBuildRequest(
        rc_id="RC-1.2.0-1", sut_version="1.2.0",
        requirements_set_version="QCR-2026-11-25", twin_fidelity_reference="FID-1",
    )))
    assert report["source"] == "database_snapshot"
    assert report["exit_criteria"]["mandatory_qcr"]["satisfied"] is True
    assert report["exit_criteria"]["mutation_score"]["satisfied"] is False
    assert report["eligible"] is False
