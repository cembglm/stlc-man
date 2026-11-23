"""Append-only lifecycle persistence with human approval gates."""

from typing import Any, Dict

from models.ifarlab_lifecycle import PatchRecord, PromotionRecord, RCReport


async def insert_immutable(collection, identity: Dict[str, str], record: Dict[str, Any]):
    existing = await collection.find_one(identity)
    if existing:
        raise ValueError("record identifier already exists; lifecycle records are append-only")
    await collection.insert_one(record)
    return record


async def save_patch(db, patch: PatchRecord):
    return await insert_immutable(
        db.patches, {"patch_id": patch.patch_id}, patch.model_dump(mode="json")
    )


async def save_rc_report(db, report: RCReport):
    return await insert_immutable(
        db.rc_reports, {"rc_id": report.rc_id}, report.model_dump(mode="json")
    )


async def save_promotion(db, promotion: PromotionRecord):
    rc = await db.rc_reports.find_one({"rc_id": promotion.rc_id})
    if not rc:
        raise ValueError("promotion references an unknown RC report")
    return await insert_immutable(
        db.promotions,
        {"promotion_id": promotion.promotion_id},
        promotion.model_dump(mode="json"),
    )
