"""MongoDB persistence for append-only traceability and IFARLAB results."""

import uuid
from collections import defaultdict
from datetime import timezone
from datetime import datetime
from typing import Any, Dict, List, Optional
from pymongo import ReturnDocument

from core.database import get_database
from models.traceability import IFARLABResult, RequirementSet, SubmissionManifest, utc_now
from services.traceability_contract import canonical_json_bytes, contract_sha256, sha256_bytes
from services.verdict_engine import aggregate_requirement, evaluate_test


GENERAL_RULES = [
    {"rule_id": "SAFETY-NO-COLLISION", "metric": "collision_count", "operator": "==", "threshold": 0, "unit": "count"},
    {"rule_id": "SAFETY-NO-JOINT-LIMIT", "metric": "joint_limit_violation_count", "operator": "==", "threshold": 0, "unit": "count"},
    {"rule_id": "SAFETY-NO-VELOCITY-LIMIT", "metric": "velocity_limit_violation_count", "operator": "==", "threshold": 0, "unit": "count"},
    {"rule_id": "SAFETY-NO-ACCELERATION-LIMIT", "metric": "acceleration_limit_violation_count", "operator": "==", "threshold": 0, "unit": "count"},
    {"rule_id": "VALIDITY-SCENE-CLEAN", "metric": "scene_clean", "operator": "==", "threshold": True, "unit": None},
    {"rule_id": "VALIDITY-RESET-SUCCESS", "metric": "reset_status", "operator": "==", "threshold": "success", "unit": None},
]


def public(document: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not document:
        return None
    value = dict(document)
    value.pop("_id", None)
    for key, item in list(value.items()):
        if hasattr(item, "isoformat"):
            value[key] = item.isoformat()
    return value


class TraceabilityService:
    async def _db(self):
        return await get_database()

    @staticmethod
    def _routing_events(result: IFARLABResult, evaluations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        events = []
        for evaluation in evaluations:
            base = f"{result.run_id}:{evaluation.get('test_case_id')}"
            cause = evaluation.get("fail_cause")
            binding_verdict = evaluation.get("authoritative_verdict") or evaluation.get("final_verdict")
            if str(binding_verdict).upper() == "FAIL" and cause:
                kind = {"sut": "defect", "test_artifact": "regeneration", "infrastructure": "infrastructure_notification"}[cause]
                requirement_ids = evaluation.get("requirement_ids") or [None]
                for requirement_id in requirement_ids if kind == "defect" else [None]:
                    key = f"{base}:{kind}:{requirement_id or '-'}"
                    events.append({
                        "routing_key": key, "kind": kind, "run_id": result.run_id,
                        "submission_id": result.submission_id,
                        "test_case_id": evaluation.get("test_case_id"),
                        "requirement_id": requirement_id,
                        "sut_version": ((evaluation.get("environment") or {}).get("sut_version")),
                        "evidence": evaluation.get("evidence", []),
                    })
            if evaluation.get("contradiction") or evaluation.get("verdict_disagreement"):
                key = f"{base}:human_review"
                events.append({
                    "routing_key": key, "kind": "human_review", "run_id": result.run_id,
                    "submission_id": result.submission_id,
                    "test_case_id": evaluation.get("test_case_id"),
                    "contradiction": evaluation.get("contradiction", False),
                    "verdict_disagreement": evaluation.get("verdict_disagreement", False),
                    "authoritative_verdict": evaluation.get("authoritative_verdict"),
                    "stlc_verdict": evaluation.get("stlc_verdict"),
                })
        return events

    async def _materialize_routing(self, db, events: List[Dict[str, Any]]) -> None:
        """Materialize the delivery-embedded outbox idempotently.

        The authoritative IFARLAB verdict is never modified. Human review only
        records the disagreement and its later resolution.
        """
        for event in events:
            kind, key = event["kind"], event["routing_key"]
            if kind == "defect":
                collection = db.defects
                identity = {"routing_key": key}
                digest = int(sha256_bytes(key.encode("utf-8"))[:8], 16) % 10000
                record = {
                    **event, "defect_id": f"D-{datetime.now().year}-{digest:04d}",
                    "status": "open", "severity": "untriaged",
                    "symptom": "Authoritative IFARLAB verdict reported a SUT failure.",
                }
            elif kind == "regeneration":
                collection, identity = db.test_regeneration_queue, {"routing_key": key}
                record = {**event, "status": "pending", "version_increment_required": True}
            elif kind == "infrastructure_notification":
                collection, identity = db.infrastructure_notifications, {"routing_key": key}
                record = {**event, "status": "pending_ifarlab_notification"}
            else:
                collection, identity = db.review_queue, {"routing_key": key}
                record = {
                    **event, "review_id": f"REV-{sha256_bytes(key.encode('utf-8'))[:12]}",
                    "status": "pending", "binding_source": "IFARLAB",
                }
            if not await collection.find_one(identity):
                await collection.insert_one(record)

    async def next_submission_id(self) -> str:
        db = await self._db()
        day = datetime.now().date().isoformat()
        counter = await db.traceability_counters.find_one_and_update(
            {"_id": f"submission:{day}"}, {"$inc": {"sequence": 1}},
            upsert=True, return_document=ReturnDocument.AFTER,
        )
        from services.traceability_contract import format_submission_id
        return format_submission_id(day, counter["sequence"])

    async def _record_regression_comparison(
        self, db, submission: Optional[Dict[str, Any]], result: IFARLABResult,
        evaluations: List[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        """Compare a queued regression run with its immutable source submission."""
        if not submission or not submission.get("regression_source_submission_id"):
            return None
        baseline_id = submission["regression_source_submission_id"]
        candidate_by_case = {item.get("test_case_id"): item for item in evaluations}
        baseline_rows = [
            item async for item in db.verification_verdicts.find({"submission_id": baseline_id})
        ]
        latest_baseline: Dict[str, Dict[str, Any]] = {}
        for item in baseline_rows:
            latest_baseline[item.get("test_case_id")] = item
        rows = []
        for test_case_id, candidate in candidate_by_case.items():
            baseline = latest_baseline.get(test_case_id)
            baseline_verdict = (baseline or {}).get("authoritative_verdict") or (baseline or {}).get("final_verdict")
            candidate_verdict = candidate.get("authoritative_verdict") or candidate.get("final_verdict")
            classification = (
                "regression" if baseline_verdict == "PASS" and candidate_verdict == "FAIL" else
                "fixed" if baseline_verdict == "FAIL" and candidate_verdict == "PASS" else
                "unchanged" if baseline_verdict == candidate_verdict else "not_comparable"
            )
            rows.append({
                "test_case_id": test_case_id, "baseline_verdict": baseline_verdict,
                "candidate_verdict": candidate_verdict, "classification": classification,
            })
        comparison = {
            "comparison_id": f"REGCMP-{result.run_id}",
            "campaign_id": submission.get("regression_campaign_id"),
            "sut_version": ((submission.get("manifest") or {}).get("sut") or {}).get("version"),
            "baseline_submission_id": baseline_id,
            "candidate_submission_id": result.submission_id,
            "candidate_run_id": result.run_id,
            "created_at": utc_now(), "rows": rows,
            "regression_count": sum(item["classification"] == "regression" for item in rows),
            "fixed_count": sum(item["classification"] == "fixed" for item in rows),
        }
        if not await db.regression_comparisons.find_one({"comparison_id": comparison["comparison_id"]}):
            await db.regression_comparisons.insert_one(comparison)
        return comparison

    async def save_requirement_set(self, requirement_set: RequirementSet) -> Dict[str, Any]:
        db = await self._db()
        payload = requirement_set.model_dump(mode="json")
        digest = sha256_bytes(canonical_json_bytes(payload))
        same_version = await db.requirement_sets.find_one({
            "requirements_set_version": requirement_set.requirements_set_version
        })
        if same_version:
            if same_version.get("content_sha256") != digest:
                raise ValueError(
                    "requirements_set_version already exists with different content"
                )
            raise ValueError("requirements_set_version already exists")
        existing = await db.requirement_sets.find_one({"content_sha256": digest})
        if existing:
            return public(existing)
        now = utc_now()
        await db.requirement_sets.update_many({"is_current": True}, {"$set": {"is_current": False}})
        record = {
            **payload, "content_sha256": digest, "is_current": True,
            "created_at": now, "event_id": f"REQSET-{uuid.uuid4().hex}",
        }
        await db.requirement_sets.insert_one(record)
        await db.traceability_events.insert_one({
            "event_id": f"EVT-{uuid.uuid4().hex}", "event_type": "requirement_set.created",
            "occurred_at": now, "requirements_set_version": requirement_set.requirements_set_version,
            "content_sha256": digest,
        })
        return public(record)

    async def current_requirement_set(self, version: Optional[str] = None) -> Optional[Dict[str, Any]]:
        db = await self._db()
        query = {"requirements_set_version": version} if version else {"is_current": True}
        return public(await db.requirement_sets.find_one(query, sort=[("created_at", -1)]))

    async def save_submission(self, manifest: SubmissionManifest, code: str) -> Dict[str, Any]:
        db = await self._db()
        manifest_payload = manifest.model_dump(mode="json")
        existing = await db.traceability_submissions.find_one({"submission_id": manifest.submission_id})
        if existing:
            suffix = " with different content" if (
                existing["manifest"] != manifest_payload or existing["code"] != code
            ) else ""
            raise ValueError("submission_id already exists" + suffix)
        now = utc_now()
        record = {
            "submission_id": manifest.submission_id, "revision": manifest.revision,
            "manifest": manifest_payload, "code": code, "created_at": now,
            "submission_acceptance_status": "pending", "supersedes_revision": manifest.revision - 1 or None,
        }
        await db.traceability_submissions.insert_one(record)
        await db.traceability_events.insert_one({
            "event_id": f"EVT-{uuid.uuid4().hex}", "event_type": "submission.created",
            "occurred_at": now, "submission_id": manifest.submission_id,
            "revision": manifest.revision, "code_sha256": manifest.code_sha256,
        })
        return public(record)

    async def submission(self, submission_id: str) -> Optional[Dict[str, Any]]:
        db = await self._db()
        return public(await db.traceability_submissions.find_one(
            {"submission_id": submission_id}, sort=[("revision", -1)]
        ))

    @staticmethod
    def _rules(requirement_set: Dict[str, Any], manifest_test: Dict[str, Any]) -> List[Dict[str, Any]]:
        rules = list(GENERAL_RULES)
        req_by_id = {item["id"]: item for item in requirement_set.get("requirements", [])}
        for requirement_id in manifest_test.get("requirements", []):
            for index, criterion in enumerate(req_by_id.get(requirement_id, {}).get("acceptance", []), 1):
                rules.append({
                    **criterion,
                    "rule_id": criterion.get("rule_id") or f"{requirement_id}-{index}",
                    "requirement_id": requirement_id,
                })
        oracle = manifest_test.get("oracle") or {}
        if "joint_tolerance_rad" in oracle:
            rules.append({"rule_id": "ORACLE-JOINT-TOLERANCE", "metric": "final_joint_error_rad", "operator": "<=", "threshold": oracle["joint_tolerance_rad"], "unit": "rad"})
        if manifest_test.get("expected_outcome") == "reject":
            rules.append({"rule_id": "ORACLE-ACTION-REJECTED", "metric": "action_rejected", "operator": "==", "threshold": True, "unit": None})
            if manifest_test.get("expected_reason"):
                rules.append({"rule_id": "ORACLE-REJECTION-REASON", "metric": "rejection_reason", "operator": "==", "threshold": manifest_test["expected_reason"], "unit": None})
        return rules

    async def ingest_result(self, result: IFARLABResult) -> Dict[str, Any]:
        db = await self._db()
        payload = result.model_dump(mode="json")
        delivery_sha = sha256_bytes(canonical_json_bytes(payload))
        same_run = await db.ifarlab_result_deliveries.find_one({"payload.run_id": result.run_id})
        if same_run:
            if same_run.get("delivery_sha256") != delivery_sha:
                raise ValueError("run_id already exists with different result content")
            response = public(same_run)
            await self._materialize_routing(db, same_run.get("routing_events", []))
            response["idempotent_replay"] = True
            return response
        duplicate = await db.ifarlab_result_deliveries.find_one({"delivery_sha256": delivery_sha})
        if duplicate:
            response = public(duplicate)
            await self._materialize_routing(db, duplicate.get("routing_events", []))
            response["idempotent_replay"] = True
            return response

        submission = await self.submission(result.submission_id)
        link_status, rejection_reasons = "linked", []
        if not submission:
            link_status, rejection_reasons = "unlinked", ["unknown_submission_id"]
        else:
            manifest = submission["manifest"]
            if manifest["code_sha256"] != result.code_sha256: rejection_reasons.append("code_hash_mismatch")
            if manifest["contract_sha256"] != result.contract_sha256: rejection_reasons.append("contract_hash_mismatch")
            if manifest["requirements_set_version"] != result.requirements_set_version: rejection_reasons.append("requirements_version_mismatch")
            if rejection_reasons: link_status = "rejected"

        requirement_set = await self.current_requirement_set(result.requirements_set_version)
        manifest_tests = {
            item["test_case_id"]: item for item in (submission or {}).get("manifest", {}).get("tests", [])
        }
        evaluations = []
        for test_result in payload["test_results"]:
            mapping = manifest_tests.get(test_result["test_case_id"])
            if not mapping:
                evaluations.append({"test_case_id": test_result["test_case_id"], "final_verdict": "INCONCLUSIVE", "issues": ["unknown_test_case_mapping"], "explanation": "The result cannot be linked to the submitted manifest."})
                continue
            admission = (test_result.get("admission") or result.submission_status or "ACCEPTED").upper()
            if link_status != "linked" or admission == "REJECTED":
                evaluations.append({
                    "verdict_id": f"V-{uuid.uuid4().hex}", "submission_id": result.submission_id,
                    "run_id": result.run_id, "test_case_id": test_result["test_case_id"],
                    "requirement_ids": mapping.get("requirements", []), "evaluated_at": utc_now(),
                    "admission": admission, "stlc_verdict": "INCONCLUSIVE", "final_verdict": "INCONCLUSIVE",
                    "authoritative_verdict": test_result.get("external_verdict"),
                    "issues": rejection_reasons or ["submission_rejected"],
                    "explanation": "The submission was not admitted for robot execution.",
                })
                continue
            rules = self._rules(requirement_set or {}, mapping)
            code_quality = (submission.get("manifest", {}).get("code_quality") or {}).get("verdict") or "not_recorded"
            reported_code_quality = test_result.get("code_quality_verdict") or (payload.get("code_quality") or {}).get("verdict")
            quality_mismatch = bool(reported_code_quality and reported_code_quality.lower() != code_quality.lower())
            validity = dict(test_result.get("validity", {}))
            execution_status = str(test_result.get("status", "")).lower()
            if execution_status not in {"completed", "passed", "failed"}:
                validity[execution_status if execution_status in {"skipped", "blocked"} else "not_executed"] = True
            if (test_result.get("validity_status") or "").upper() == "INCONCLUSIVE":
                validity["trustworthy"] = False
            evaluated = evaluate_test(
                rules=rules, metrics=test_result.get("metrics", {}),
                assertion_result=test_result.get("assertion_result"), robot_verdict=test_result.get("robot_verdict"),
                evidence=test_result.get("evidence", []), validity=validity,
                code_quality_verdict=code_quality,
            )
            authoritative = test_result.get("external_verdict")
            evaluations.append({
                "verdict_id": f"V-{uuid.uuid4().hex}", "submission_id": result.submission_id,
                "run_id": result.run_id, "test_case_id": test_result["test_case_id"],
                "requirement_ids": mapping.get("requirements", []), "evaluated_at": utc_now(),
                "external_executed_at": result.executed_at,
                "requirements_set_version": result.requirements_set_version,
                "code_sha256": result.code_sha256,
                "environment": payload.get("environment", {}),
                "execution_status": execution_status,
                "evidence": test_result.get("evidence", []), **evaluated,
                "admission": admission, "stlc_verdict": evaluated["final_verdict"],
                "authoritative_verdict": authoritative,
                "reported_code_quality": reported_code_quality,
                "code_quality_mismatch": quality_mismatch,
                "external_robot_verdict": test_result.get("robot_verdict"),
                "fail_cause": test_result.get("fail_cause") or evaluated.get("fail_cause"),
                "verification_level": result.verification_level,
                "verdict_disagreement": bool(authoritative and evaluated["final_verdict"] != authoritative.upper()),
            })

        now = utc_now()
        routing_events = self._routing_events(result, evaluations)
        regression_comparison = None
        if hasattr(db, "regression_comparisons"):
            regression_comparison = await self._record_regression_comparison(
                db, submission, result, evaluations
            )
        record = {
            "delivery_id": f"DEL-{uuid.uuid4().hex}", "delivery_sha256": delivery_sha,
            "received_at": now, "link_status": link_status, "rejection_reasons": rejection_reasons,
            "payload": payload, "evaluations": evaluations, "routing_events": routing_events,
            "regression_comparison": regression_comparison,
        }
        await db.ifarlab_result_deliveries.insert_one(record)
        if evaluations:
            await db.verification_verdicts.insert_many(evaluations)
        await self._materialize_routing(db, routing_events)
        await db.traceability_events.insert_one({
            "event_id": f"EVT-{uuid.uuid4().hex}", "event_type": "external_result.received",
            "occurred_at": now, "submission_id": result.submission_id, "run_id": result.run_id,
            "delivery_sha256": delivery_sha, "link_status": link_status,
        })
        return public(record)

    async def dashboard(self, search: Optional[str] = None, verdict: Optional[str] = None) -> Dict[str, Any]:
        db = await self._db()
        req_set = await self.current_requirement_set()
        requirements = (req_set or {}).get("requirements", [])
        submissions = [public(item) async for item in db.traceability_submissions.find({})]
        verdict_records = [public(item) async for item in db.verification_verdicts.find({})]
        deliveries = [public(item) async for item in db.ifarlab_result_deliveries.find({})]
        latest = {}
        for item in sorted(verdict_records, key=lambda row: row.get("external_executed_at") or row.get("evaluated_at", "")):
            latest[(item.get("submission_id"), item["test_case_id"])] = item
        tests_by_req = defaultdict(list)
        rows = []
        for submission in submissions:
            manifest = submission["manifest"]
            for test in manifest.get("tests", []):
                match = latest.get((manifest["submission_id"], test["test_case_id"]))
                for requirement_id in test.get("requirements", []): tests_by_req[requirement_id].append(match)
                rows.append({
                    "requirement_ids": test.get("requirements", []), "test_case_id": test["test_case_id"],
                    "scenario_id": test.get("scenario_id"), "generation_run_id": manifest.get("generation_run_id"),
                    "function": test["function"], "llm": manifest.get("generation", {}).get("model") or "Not Recorded",
                    "provider": manifest.get("generation", {}).get("provider") or "Not Recorded",
                    "code_sha256": manifest["code_sha256"], "submission_id": manifest["submission_id"],
                    "run_id": (match or {}).get("run_id"), "verdict": (match or {}).get("authoritative_verdict") or (match or {}).get("final_verdict", "NOT_VERIFIED"),
                    "code_quality": manifest.get("code_quality", {}).get("verdict", "not_recorded"),
                    "explanation": (match or {}).get("explanation"), "applied_rules": (match or {}).get("applied_rules", []),
                    "evidence": (match or {}).get("evidence", []), "contradiction": (match or {}).get("contradiction", False),
                    "verdict_engine_version": (match or {}).get("verdict_engine_version"),
                    "rule_set_version": (match or {}).get("rule_set_version"),
                    "assertion_result": (match or {}).get("assertion_result"),
                    "robot_evaluation": (match or {}).get("independent_robot_evaluation"),
                    "execution_validity": (match or {}).get("execution_validity"),
                    "stlc_verdict": (match or {}).get("stlc_verdict"),
                    "authoritative_verdict": (match or {}).get("authoritative_verdict"),
                    "admission": (match or {}).get("admission"),
                })
        states = {}
        current_version = (req_set or {}).get("requirements_set_version")
        for req in requirements:
            associated = tests_by_req.get(req["id"], [])
            linked_submissions = [
                s for s in submissions
                if any(req["id"] in t.get("requirements", []) for t in s["manifest"].get("tests", []))
            ]
            requirement_inputs = []
            for item in associated:
                item = item or {}
                item_verdict = item.get("authoritative_verdict") or item.get("final_verdict", "INCONCLUSIVE")
                if str(item_verdict).upper() == "FAIL" and item.get("fail_cause") != "sut":
                    # Unknown and non-SUT causes must never accuse the product.
                    item_verdict = "INCONCLUSIVE"
                requirement_inputs.append(item_verdict)
            states[req["id"]] = aggregate_requirement(
                requirement_inputs, bool(associated),
                stale=bool(linked_submissions) and not any(s["manifest"]["requirements_set_version"] == current_version for s in linked_submissions),
            )
            if not any(req["id"] in row["requirement_ids"] for row in rows):
                rows.append({"requirement_ids": [req["id"]], "test_case_id": None, "llm": "Not Recorded", "code_sha256": None, "submission_id": None, "run_id": None, "verdict": states[req["id"]], "code_quality": "not_recorded", "evidence": [], "applied_rules": []})
        if search:
            needle = search.lower()
            rows = [row for row in rows if needle in str(row).lower()]
        if verdict:
            rows = [row for row in rows if row.get("verdict") == verdict.upper()]
        total, covered, passed = len(requirements), sum(bool(tests_by_req.get(r["id"])) for r in requirements), sum(states.get(r["id"]) == "PASS" for r in requirements)
        quality_distribution = defaultdict(int)
        llm_distribution = defaultdict(int)
        execution_distribution = defaultdict(int)
        for row in rows:
            quality_distribution[row.get("code_quality", "not_recorded")] += 1
            llm_distribution[row.get("llm", "Not Recorded")] += int(bool(row.get("test_case_id")))
            execution_distribution[row.get("verdict", "NOT_VERIFIED")] += 1
        robot_metrics_received = sum(
            len(test.get("metrics", {}))
            for delivery in deliveries for test in delivery.get("payload", {}).get("test_results", [])
        )
        traceability_gaps = sum(
            not row.get("requirement_ids") or not row.get("test_case_id") or (row.get("run_id") and not row.get("evidence"))
            for row in rows
        )
        return {
            "scope": {"requirements_set_version": current_version, "contract_sha256": contract_sha256()},
            "metrics": {"total_requirements": total, "covered_requirements": covered, "uncovered_requirements": total-covered, "verified_requirements": passed, "coverage_percentage": (covered/total*100 if total else 0), "verification_percentage": (passed/total*100 if total else 0), "requirement_states": {state: list(states.values()).count(state) for state in ["PASS", "FAIL", "NOT_VERIFIED", "NOT_COVERED", "STALE"]}, "total_generated_test_cases": sum(len(s["manifest"].get("tests", [])) for s in submissions), "external_submissions": len({s["submission_id"] for s in submissions}), "robot_metrics_received": robot_metrics_received, "traceability_gaps": traceability_gaps, "code_quality_distribution": dict(quality_distribution), "tests_by_llm": dict(llm_distribution), "execution_results": dict(execution_distribution)},
            "requirements": [{**req, "verification_state": states.get(req["id"], "NOT_COVERED")} for req in requirements],
            "rows": rows,
        }

    async def reverse_queries(self) -> Dict[str, Any]:
        """Return explicit reverse links without hiding broken chains."""
        db = await self._db()
        submissions = [public(item) async for item in db.traceability_submissions.find({})]
        verdicts = [public(item) async for item in db.verification_verdicts.find({})]
        defects = [public(item) async for item in db.defects.find({})]
        patches = [public(item) async for item in db.patches.find({})]
        rc_reports = [public(item) async for item in db.rc_reports.find({})]
        promotions = [public(item) async for item in db.promotions.find({})]
        verdict_by_submission_case = {
            (item.get("submission_id"), item.get("test_case_id")): item for item in verdicts
        }
        matrix, broken = [], []
        for submission in submissions:
            manifest = submission.get("manifest", {})
            sut_version = (manifest.get("sut") or {}).get("version")
            for test in manifest.get("tests", []):
                verdict = verdict_by_submission_case.get((manifest.get("submission_id"), test.get("test_case_id")))
                for requirement_id in test.get("requirements", []):
                    row = {
                        "requirement_id": requirement_id,
                        "test_case_id": test.get("test_case_id"),
                        "sut_version": sut_version,
                        "submission_id": manifest.get("submission_id"),
                        "run_id": (verdict or {}).get("run_id"),
                        "verdict": (verdict or {}).get("authoritative_verdict") or (verdict or {}).get("final_verdict") or "NOT_VERIFIED",
                        "verification_level": (verdict or {}).get("verification_level"),
                        "evidence": (verdict or {}).get("evidence", []),
                    }
                    matrix.append(row)
                    missing = [name for name in ("sut_version", "run_id") if not row.get(name)]
                    if missing:
                        broken.append({**row, "missing_links": missing})
        patch_by_defect = defaultdict(list)
        for patch in patches:
            patch_by_defect[patch.get("defect_id")].append(patch)
        defect_chains = [{
            **defect,
            "patches": patch_by_defect.get(defect.get("defect_id"), []),
            "resolved_in_versions": sorted({p.get("applied_in_version") for p in patch_by_defect.get(defect.get("defect_id"), []) if p.get("applied_in_version")}),
        } for defect in defects]
        rc_by_id = {item.get("rc_id"): item for item in rc_reports}
        promotion_chains = [{
            **promotion,
            "rc_report": rc_by_id.get(promotion.get("rc_id")),
            "chain_complete": bool(rc_by_id.get(promotion.get("rc_id"))),
        } for promotion in promotions]
        return {
            "matrix": matrix,
            "requirement_tests": {
                requirement_id: sorted({row["test_case_id"] for row in matrix if row["requirement_id"] == requirement_id})
                for requirement_id in sorted({row["requirement_id"] for row in matrix})
            },
            "failed_by_sut_version": {
                version: sorted({row["requirement_id"] for row in matrix if row["sut_version"] == version and row["verdict"] == "FAIL"})
                for version in sorted({row["sut_version"] for row in matrix if row["sut_version"]})
            },
            "defect_patch_version_chains": defect_chains,
            "promotion_requirement_chains": promotion_chains,
            "broken_links": broken,
        }


traceability_service = TraceabilityService()
