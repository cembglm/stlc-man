"""Validation and immutable persistence for IFARLAB SUT release packages."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any, Dict

from models.ifarlab_lifecycle import SUTRelease
from models.traceability import RequirementSet


class SUTPackageError(ValueError):
    pass


def validate_sut_package(
    source_archive: bytes, release_payload: Dict[str, Any], requirements_payload: Dict[str, Any]
) -> tuple[SUTRelease, RequirementSet]:
    release = SUTRelease(**release_payload)
    actual_sha = hashlib.sha256(source_archive).hexdigest()
    if actual_sha != release.source_sha256:
        raise SUTPackageError("source archive sha256 does not match sut_release.json")
    requirements = RequirementSet(**requirements_payload)
    if release.requirements_set_version != requirements.requirements_set_version:
        raise SUTPackageError("SUT release and requirements set versions do not match")
    invalid = [item.id for item in requirements.requirements if not item.id.startswith("QCR-")]
    if invalid:
        raise SUTPackageError("new SUT packages accept only QCR-NNN requirements: " + ", ".join(invalid))
    return release, requirements


async def persist_sut_package(
    db, source_archive: bytes, release_payload: Dict[str, Any], requirements_payload: Dict[str, Any]
) -> Dict[str, Any]:
    release, requirements = validate_sut_package(source_archive, release_payload, requirements_payload)
    key = {"sut_id": release.sut_id, "version": release.version}
    existing = await db.sut_releases.find_one(key)
    if existing:
        if existing.get("source_sha256") != release.source_sha256:
            raise SUTPackageError("same SUT version already exists with a different source sha256")
        raise SUTPackageError("same SUT version already exists")
    missing_defects = []
    for defect_id in release.fixes:
        if not await db.defects.find_one({"defect_id": defect_id}):
            missing_defects.append(defect_id)
    if missing_defects:
        raise SUTPackageError("fixes reference unknown defects: " + ", ".join(missing_defects))
    now = datetime.now(timezone.utc)
    record = {
        **release.model_dump(mode="json"),
        "requirements": requirements.model_dump(mode="json"),
        "source_archive": source_archive,
        "source_read_only": True,
        "imported_at": now,
    }
    await db.sut_releases.insert_one(record)
    return record
