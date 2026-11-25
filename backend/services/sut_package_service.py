"""Validation and immutable persistence for IFARLAB SUT release packages."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any, Dict
from pydantic import ValidationError
from pymongo import ReturnDocument

from models.ifarlab_lifecycle import SUTRelease
from models.traceability import RequirementSet


class SUTPackageError(ValueError):
    pass


async def queue_regression_campaign(db, release: SUTRelease) -> Dict[str, Any]:
    """Clone the current suite as append-only submissions for a new SUT release.

    Dispatch remains behind the normal validator/SSH boundary; importing a SUT
    release never bypasses acceptance control or contacts IFARLAB directly.
    """
    now = datetime.now(timezone.utc)
    day = now.date().isoformat()
    campaign_id = f"REG-{now.strftime('%Y%m%dT%H%M%S%fZ')}"
    source_rows = [
        item async for item in db.traceability_submissions.find({
            "manifest.requirements_set_version": release.requirements_set_version
        })
    ]
    # Keep only the newest revision of each source submission.
    latest = {}
    for row in source_rows:
        key = row.get("submission_id") or row.get("manifest", {}).get("submission_id")
        if key and row.get("revision", row.get("manifest", {}).get("revision", 1)) >= latest.get(key, {}).get("revision", 0):
            latest[key] = row
    queued = []
    for source in latest.values():
        counter = await db.traceability_counters.find_one_and_update(
            {"_id": f"submission:{day}"}, {"$inc": {"sequence": 1}},
            upsert=True, return_document=ReturnDocument.AFTER,
        )
        submission_id = f"S-{day}-{counter['sequence']:04d}"
        manifest = dict(source["manifest"])
        manifest.update({
            "submission_id": submission_id, "revision": 1,
            "sut": {
                "sut_id": release.sut_id, "version": release.version,
                "commit": release.commit, "source_sha256": release.source_sha256,
            },
        })
        record = {
            "submission_id": submission_id, "revision": 1, "manifest": manifest,
            "code": source["code"], "created_at": now,
            "submission_acceptance_status": "pending",
            "regression_campaign_id": campaign_id,
            "regression_source_submission_id": source.get("submission_id"),
        }
        await db.traceability_submissions.insert_one(record)
        queued.append({
            "submission_id": submission_id,
            "test_case_ids": [item["test_case_id"] for item in manifest.get("tests", [])],
            "dispatch_status": "queued_for_validated_ssh_dispatch",
        })
    campaign = {
        "campaign_id": campaign_id, "sut_id": release.sut_id,
        "sut_version": release.version, "requirements_set_version": release.requirements_set_version,
        "created_at": now, "status": "queued" if queued else "empty_suite",
        "submissions": queued,
    }
    await db.regression_campaigns.insert_one(campaign)
    return campaign


def validate_sut_package(
    source_archive: bytes, release_payload: Dict[str, Any], requirements_payload: Dict[str, Any]
) -> tuple[SUTRelease, RequirementSet]:
    try:
        release = SUTRelease(**release_payload)
        requirements = RequirementSet(**requirements_payload)
    except ValidationError as exc:
        raise SUTPackageError(str(exc)) from exc
    actual_sha = hashlib.sha256(source_archive).hexdigest()
    if actual_sha != release.source_sha256:
        raise SUTPackageError("source archive sha256 does not match sut_release.json")
    if release.requirements_set_version != requirements.requirements_set_version:
        raise SUTPackageError("SUT release and requirements set versions do not match")
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
    if hasattr(db, "traceability_submissions") and hasattr(db, "regression_campaigns"):
        record["regression_campaign"] = await queue_regression_campaign(db, release)
    return record
