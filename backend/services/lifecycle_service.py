"""Append-only lifecycle persistence with human approval gates."""

from typing import Any, Dict

from models.ifarlab_lifecycle import (
    MutantRequest, MutantResult, PatchRecord, PromotionRecord, RCBuildRequest, RCReport, ReviewDecision,
)


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


async def build_rc_report(db, request: RCBuildRequest):
    """Derive RC exit criteria from one database snapshot instead of client claims."""
    requirement_set = await db.requirement_sets.find_one({
        "requirements_set_version": request.requirements_set_version
    })
    if not requirement_set:
        raise ValueError("RC references an unknown requirement set")
    verdicts = [item async for item in db.verification_verdicts.find({})]
    latest_by_requirement = {}
    verdicts.sort(key=lambda item: str(item.get("external_executed_at") or item.get("evaluated_at") or ""))
    for verdict in verdicts:
        environment = verdict.get("environment") or {}
        if environment.get("sut_version") != request.sut_version:
            continue
        value = verdict.get("authoritative_verdict") or verdict.get("final_verdict")
        for requirement_id in verdict.get("requirement_ids", []):
            latest_by_requirement[requirement_id] = value
    mandatory = [
        item["id"] for item in requirement_set.get("requirements", [])
        if item.get("priority", "mandatory") == "mandatory"
    ]
    open_defects = [
        item async for item in db.defects.find({"sut_version": request.sut_version})
        if item.get("status", "open") != "closed" and item.get("severity") in {"high", "critical"}
    ]
    regressions = [
        item async for item in db.regression_comparisons.find({"sut_version": request.sut_version})
        if item.get("regression_count", 0) > 0
    ]
    mutant_requests = [item async for item in db.mutant_requests.find({"base_version": request.sut_version})]
    mutant_ids = {item.get("mutant_id") for item in mutant_requests}
    mutant_results = [
        item async for item in db.mutant_results.find({}) if item.get("mutant_id") in mutant_ids
    ]
    killed = sum(item.get("outcome") == "killed" for item in mutant_results)
    survived = sum(item.get("outcome") == "survived" for item in mutant_results)
    mutation_score = (killed / (killed + survived) * 100) if killed + survived else None
    criteria = {
        "mandatory_qcr": {
            "satisfied": bool(mandatory) and all(latest_by_requirement.get(item) == "PASS" for item in mandatory),
            "value": {item: latest_by_requirement.get(item, "NOT_VERIFIED") for item in mandatory},
            "evidence": sorted(latest_by_requirement),
        },
        "open_high_critical_defects": {
            "satisfied": not open_defects, "value": len(open_defects),
            "evidence": [item.get("defect_id") for item in open_defects],
        },
        "regressions": {
            "satisfied": not regressions, "value": sum(item.get("regression_count", 0) for item in regressions),
            "evidence": [item.get("comparison_id") for item in regressions],
        },
        "mutation_score": {
            "satisfied": mutation_score is not None and mutation_score >= request.mutation_score_threshold,
            "value": mutation_score,
            "evidence": sorted(mutant_ids),
        },
    }
    report = RCReport(
        rc_id=request.rc_id, sut_version=request.sut_version,
        exit_criteria=criteria, requirement_verdicts={
            item["id"]: latest_by_requirement.get(item["id"], "NOT_VERIFIED")
            for item in requirement_set.get("requirements", [])
        },
        evidence_references=sorted({e for item in criteria.values() for e in item["evidence"] if e}),
        twin_fidelity_reference=request.twin_fidelity_reference,
        source="database_snapshot",
    )
    return await save_rc_report(db, report)


async def save_promotion(db, promotion: PromotionRecord):
    rc = await db.rc_reports.find_one({"rc_id": promotion.rc_id})
    if not rc:
        raise ValueError("promotion references an unknown RC report")
    if not rc.get("eligible", False):
        raise ValueError("promotion references an ineligible RC report")
    if rc.get("source") != "database_snapshot":
        raise ValueError("promotion requires an RC report derived from a database snapshot")
    return await insert_immutable(
        db.promotions,
        {"promotion_id": promotion.promotion_id},
        promotion.model_dump(mode="json"),
    )


async def save_mutant_request(db, request: MutantRequest):
    return await insert_immutable(
        db.mutant_requests, {"mutant_id": request.mutant_id}, request.model_dump(mode="json")
    )


async def save_mutant_result(db, result: MutantResult):
    request = await db.mutant_requests.find_one({"mutant_id": result.mutant_id})
    if not request:
        raise ValueError("mutant result references an unknown mutant request")
    return await insert_immutable(
        db.mutant_results, {"mutant_id": result.mutant_id}, result.model_dump(mode="json")
    )


async def resolve_review(db, decision: ReviewDecision):
    review = await db.review_queue.find_one({"review_id": decision.review_id})
    if not review:
        raise ValueError("review decision references an unknown review")
    verdict = await db.verification_verdicts.find_one({"verdict_id": decision.supersedes_verdict_id})
    if not verdict:
        raise ValueError("review decision references an unknown verdict")
    if verdict.get("run_id") != review.get("run_id") or verdict.get("test_case_id") != review.get("test_case_id"):
        raise ValueError("review decision verdict does not belong to the review")
    record = decision.model_dump(mode="json")
    await insert_immutable(db.review_decisions, {"review_id": decision.review_id}, record)
    superseding = {
        **{key: value for key, value in verdict.items() if key != "_id"},
        "verdict_id": f"{decision.supersedes_verdict_id}-R",
        "final_verdict": decision.authoritative_verdict,
        "authoritative_verdict": decision.authoritative_verdict,
        "supersedes_verdict_id": decision.supersedes_verdict_id,
        "review_decision_id": decision.decision_id,
        "reviewed_by": decision.reviewer,
        "reviewed_at": decision.decided_at,
        "review_rationale": decision.rationale,
    }
    await insert_immutable(
        db.verification_verdicts, {"verdict_id": superseding["verdict_id"]}, superseding
    )
    return {"review": record, "superseding_verdict": superseding}
