import hashlib

import pytest

from services.sut_package_service import SUTPackageError, persist_sut_package, validate_sut_package


class Collection:
    def __init__(self, rows=None): self.rows = list(rows or [])
    async def find_one(self, query):
        return next((row for row in self.rows if all(row.get(k) == v for k, v in query.items())), None)
    async def insert_one(self, value): self.rows.append(dict(value))


class DB:
    def __init__(self, defects=None):
        self.sut_releases = Collection()
        self.defects = Collection(defects)


def payloads(source=b"source", *, version="1.3.0", digest=None, fixes=None, req_id="QCR-001"):
    release = {
        "schema_version": "1.0", "sut_id": "IFARLAB-QC", "version": version,
        "commit": "abc", "source_sha256": digest or hashlib.sha256(source).hexdigest(),
        "requirements_set_version": "QCR-2026-11-19", "build": {}, "fixes": fixes or [],
    }
    requirements = {
        "requirements_set_version": "QCR-2026-11-19",
        "requirements": [{"id": req_id, "version": "1.0", "type": "functional", "text": "Reject scratch"}],
    }
    return release, requirements


def drive(coroutine):
    try: coroutine.send(None)
    except StopIteration as done: return done.value
    raise AssertionError("unexpected await")


def test_valid_package_and_hash_mismatch():
    release, requirements = payloads()
    parsed, _ = validate_sut_package(b"source", release, requirements)
    assert parsed.version == "1.3.0"
    with pytest.raises(SUTPackageError, match="sha256"):
        validate_sut_package(b"changed", release, requirements)


def test_new_package_rejects_legacy_requirement_ids():
    release, requirements = payloads(req_id="FR-001")
    with pytest.raises(SUTPackageError, match="only QCR"):
        validate_sut_package(b"source", release, requirements)


def test_same_version_different_hash_is_rejected():
    db = DB()
    release, requirements = payloads()
    drive(persist_sut_package(db, b"source", release, requirements))
    other = b"other"
    release2, requirements2 = payloads(other, digest=hashlib.sha256(other).hexdigest())
    with pytest.raises(SUTPackageError, match="same SUT version"):
        drive(persist_sut_package(db, other, release2, requirements2))


def test_fixes_must_reference_known_defects():
    release, requirements = payloads(fixes=["D-2026-0007"])
    with pytest.raises(SUTPackageError, match="unknown defects"):
        drive(persist_sut_package(DB(), b"source", release, requirements))
    db = DB([{"defect_id": "D-2026-0007"}])
    assert drive(persist_sut_package(db, b"source", release, requirements))["source_read_only"] is True
