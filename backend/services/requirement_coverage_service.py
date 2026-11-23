"""Deterministic MATISSE KPI 3.4 requirement coverage aggregation.

The primary KPI is executed Digital Twin coverage. Generated or mapped tests
are useful readiness stages but never enter the KPI numerator.
"""

from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

from models.traceability import RequirementType
from services.traceability_contract import contract_sha256
from services.verdict_engine import aggregate_requirement


COVERAGE_ENGINE_VERSION = "1.0.0"
FR_TARGET = 100.0
NFR_TARGET = 80.0
VALID_EXECUTED_VERDICTS = {"PASS", "FAIL"}


def _iso(value: Any) -> Optional[str]:
    if value is None:
        return None
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


def _percentage(numerator: int, denominator: int) -> Optional[float]:
    return round(numerator / denominator * 100, 4) if denominator else None


def _metric(numerator: int, denominator: int, target: float) -> Dict[str, Any]:
    value = _percentage(numerator, denominator)
    return {
        "covered": numerator,
        "total_applicable": denominator,
        "percentage": value,
        "target_percentage": target,
        "assessment": "not_assessable" if value is None else ("achieved" if value >= target else "not_achieved"),
    }


def _active_requirements(requirement_set: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [
        requirement for requirement in requirement_set.get("requirements", [])
        if requirement.get("applicable", True)
        and requirement.get("status", "active") == "active"
    ]


def _environment_qualifies(environment: Dict[str, Any]) -> Tuple[bool, List[str]]:
    reasons = []
    if environment.get("scope", "unknown") != "digital_twin":
        reasons.append("execution_scope_is_not_digital_twin")
    if not environment.get("environment_id"):
        reasons.append("missing_environment_id")
    if not environment.get("digital_twin_id"):
        reasons.append("missing_digital_twin_id")
    if not (environment.get("registry_reference") or environment.get("provenance_sha256")):
        reasons.append("missing_environment_provenance")
    return not reasons, reasons


def _executable(code_quality: Dict[str, Any]) -> bool:
    verdict = str(code_quality.get("verdict", "not_recorded")).lower()
    syntax = str(code_quality.get("syntax", "not_recorded")).lower()
    validator = str(code_quality.get("validator", "not_recorded")).lower()
    return verdict in {"pass", "pass_with_warnings"} and syntax == "pass" and validator not in {"fail", "invalid"}


def calculate_requirement_coverage(
    requirement_set: Optional[Dict[str, Any]],
    submissions: Iterable[Dict[str, Any]],
    deliveries: Iterable[Dict[str, Any]],
    verdict_records: Iterable[Dict[str, Any]],
    *,
    project_id: Optional[str] = None,
    session_id: Optional[str] = None,
    environment_id: Optional[str] = None,
    digital_twin_id: Optional[str] = None,
) -> Dict[str, Any]:
    evaluated_at = datetime.now(timezone.utc).isoformat()
    if not requirement_set:
        return {
            "engine_version": COVERAGE_ENGINE_VERSION,
            "evaluation_timestamp": evaluated_at,
            "status": "not_assessable",
            "limitations": ["requirement_set_not_found"],
            "scope": {"requirements_set_version": None},
            "kpi": {
                "functional": _metric(0, 0, FR_TARGET),
                "non_functional": _metric(0, 0, NFR_TARGET),
            },
            "verified": {
                "functional": _metric(0, 0, FR_TARGET),
                "non_functional": _metric(0, 0, NFR_TARGET),
            },
            "stages": {}, "requirements": [], "summary": {},
        }

    set_version = requirement_set.get("requirements_set_version")
    requirements = _active_requirements(requirement_set)
    requirement_by_id = {item["id"]: item for item in requirements}
    submissions = list(submissions)
    deliveries = list(deliveries)
    verdict_records = list(verdict_records)

    def submission_in_scope(item: Dict[str, Any]) -> bool:
        manifest = item.get("manifest", {})
        return (
            manifest.get("requirements_set_version") == set_version
            and (not project_id or manifest.get("project_id") == project_id)
            and (not session_id or manifest.get("session_id") == session_id or item.get("source_session_id") == session_id)
        )

    scoped_submissions = [item for item in submissions if submission_in_scope(item)]
    submission_by_id = {item.get("submission_id") or item.get("manifest", {}).get("submission_id"): item for item in scoped_submissions}

    delivery_by_run = {}
    for delivery in deliveries:
        payload = delivery.get("payload", {})
        if delivery.get("link_status") != "linked" or payload.get("requirements_set_version") != set_version:
            continue
        environment = payload.get("environment", {})
        if environment_id and environment.get("environment_id") != environment_id:
            continue
        if digital_twin_id and environment.get("digital_twin_id") != digital_twin_id:
            continue
        delivery_by_run[(payload.get("submission_id"), payload.get("run_id"))] = delivery

    latest_verdict = {}
    for verdict in sorted(verdict_records, key=lambda item: _iso(item.get("external_executed_at") or item.get("evaluated_at")) or ""):
        key = (verdict.get("submission_id"), verdict.get("run_id"), verdict.get("test_case_id"))
        latest_verdict[key] = verdict

    chains = defaultdict(list)
    orphan_links = []
    for submission in scoped_submissions:
        manifest = submission.get("manifest", {})
        code_quality = manifest.get("code_quality", {})
        generated = bool(submission.get("code") and manifest.get("code_sha256"))
        executable = generated and _executable(code_quality)
        for test in manifest.get("tests", []):
            requirement_ids = list(dict.fromkeys(test.get("requirements", [])))
            scenario_id = test.get("scenario_id")
            for requirement_id in requirement_ids:
                if requirement_id not in requirement_by_id:
                    orphan_links.append({"requirement_id": requirement_id, "test_case_id": test.get("test_case_id"), "reason": "unknown_or_inactive_requirement"})
                    continue
                expected_version = test.get("requirement_versions", {}).get(requirement_id)
                actual_version = requirement_by_id[requirement_id].get("version")
                version_valid = not expected_version or expected_version == actual_version
                chain = {
                    "requirement_id": requirement_id,
                    "requirement_version": actual_version,
                    "scenario_id": scenario_id,
                    "test_case_id": test.get("test_case_id"),
                    "function": test.get("function"),
                    "submission_id": manifest.get("submission_id"),
                    "submission_revision": manifest.get("revision", 1),
                    "code_sha256": manifest.get("code_sha256"),
                    "mapped": bool(scenario_id and test.get("test_case_id") and version_valid),
                    "generated": bool(scenario_id and version_valid and generated),
                    "executable": bool(scenario_id and version_valid and executable),
                    "executions": [],
                    "stale": not version_valid,
                }
                for (submission_id_value, run_id, case_id), verdict in latest_verdict.items():
                    if submission_id_value != manifest.get("submission_id") or case_id != test.get("test_case_id"):
                        continue
                    delivery = delivery_by_run.get((submission_id_value, run_id))
                    environment = (delivery or {}).get("payload", {}).get("environment", {})
                    dt_eligible, exclusions = _environment_qualifies(environment)
                    final_verdict = str(verdict.get("final_verdict", "INCONCLUSIVE")).upper()
                    evidence = verdict.get("evidence", [])
                    if not chain["executable"]:
                        exclusions.append("test_code_not_executable_ready")
                    if delivery is None:
                        exclusions.append("linked_delivery_not_found_in_scope")
                    if not evidence:
                        exclusions.append("missing_execution_evidence")
                    if verdict.get("execution_validity") != "VALID":
                        exclusions.append("execution_invalid")
                    if final_verdict not in VALID_EXECUTED_VERDICTS:
                        exclusions.append("verdict_not_pass_or_fail")
                    if chain["stale"]:
                        exclusions.append("stale_requirement_version")
                    execution_valid = (
                        chain["executable"] and dt_eligible and delivery is not None and bool(evidence)
                        and verdict.get("execution_validity") == "VALID"
                        and final_verdict in VALID_EXECUTED_VERDICTS
                        and not chain["stale"]
                    )
                    chain["executions"].append({
                        "verdict_id": verdict.get("verdict_id"), "run_id": run_id,
                        "final_verdict": final_verdict, "execution_validity": verdict.get("execution_validity"),
                        "environment": environment, "evidence": evidence,
                        "dt_eligible": execution_valid,
                        "exclusions": list(dict.fromkeys(exclusions)),
                    })
                chains[requirement_id].append(chain)

    rows = []
    stage_counts = {stage: defaultdict(int) for stage in ("mapped", "generated", "executable", "executed_dt", "verified_dt")}
    for requirement in requirements:
        req_chains = chains.get(requirement["id"], [])
        valid_executions = [execution for chain in req_chains for execution in chain["executions"] if execution["dt_eligible"]]
        executed_verdicts = [execution["final_verdict"] for execution in valid_executions]
        mapped = any(chain["mapped"] for chain in req_chains)
        generated = any(chain["generated"] for chain in req_chains)
        executable = any(chain["executable"] for chain in req_chains)
        executed_dt = bool(valid_executions)
        verification_state = aggregate_requirement(executed_verdicts, covered=executed_dt, stale=any(chain["stale"] for chain in req_chains))
        verified_dt = verification_state == "PASS"
        stage = "unmapped"
        for name, active in (("mapped", mapped), ("generated", generated), ("executable", executable), ("executed_dt", executed_dt), ("verified_dt", verified_dt)):
            if active:
                stage = name
                stage_counts[name][requirement.get("type", "unclassified")] += 1
        rows.append({
            **requirement,
            "coverage_stage": stage,
            "mapped": mapped, "generated": generated, "executable": executable,
            "executed_dt": executed_dt, "verified_dt": verified_dt,
            "verification_state": verification_state,
            "traceability_chains": req_chains,
            "valid_dt_execution_count": len(valid_executions),
        })

    typed = {
        RequirementType.FUNCTIONAL.value: [row for row in rows if row.get("type") == RequirementType.FUNCTIONAL.value],
        RequirementType.NON_FUNCTIONAL.value: [row for row in rows if row.get("type") == RequirementType.NON_FUNCTIONAL.value],
        RequirementType.UNCLASSIFIED.value: [row for row in rows if row.get("type") == RequirementType.UNCLASSIFIED.value],
    }
    kpi = {
        "functional": _metric(sum(row["executed_dt"] for row in typed["functional"]), len(typed["functional"]), FR_TARGET),
        "non_functional": _metric(sum(row["executed_dt"] for row in typed["non_functional"]), len(typed["non_functional"]), NFR_TARGET),
    }
    verified = {
        "functional": _metric(sum(row["verified_dt"] for row in typed["functional"]), len(typed["functional"]), FR_TARGET),
        "non_functional": _metric(sum(row["verified_dt"] for row in typed["non_functional"]), len(typed["non_functional"]), NFR_TARGET),
    }
    return {
        "engine_version": COVERAGE_ENGINE_VERSION,
        "evaluation_timestamp": evaluated_at,
        "status": "assessed" if typed["functional"] or typed["non_functional"] else "not_assessable",
        "scope": {
            "requirements_set_version": set_version,
            "requirement_set_sha256": requirement_set.get("content_sha256"),
            "project_id": project_id, "session_id": session_id,
            "environment_id": environment_id, "digital_twin_id": digital_twin_id,
            "contract_sha256": contract_sha256(),
        },
        "kpi": kpi, "verified": verified,
        "stages": {name: dict(values) for name, values in stage_counts.items()},
        "summary": {
            "total_applicable": len(rows),
            "unclassified_requirements": len(typed["unclassified"]),
            "uncovered_requirements": sum(not row["executed_dt"] for row in rows),
            "generated_not_executed": sum(row["generated"] and not row["executed_dt"] for row in rows),
            "failed_or_inconclusive": sum(row["verification_state"] in {"FAIL", "NOT_VERIFIED"} for row in rows),
            "stale_requirements": sum(row["verification_state"] == "STALE" for row in rows),
            "orphan_links": len(orphan_links),
        },
        "requirements": rows,
        "orphan_links": orphan_links,
        "limitations": [
            "Only explicit registered Digital Twin executions with provenance and evidence enter the primary KPI.",
            "Synthetic or demonstration results must be scoped and labelled separately from project KPI claims.",
        ],
    }


class RequirementCoverageService:
    def __init__(self, traceability_service):
        self.traceability_service = traceability_service

    async def calculate(self, **filters) -> Dict[str, Any]:
        db = await self.traceability_service._db()
        requirement_set = await self.traceability_service.current_requirement_set(filters.pop("requirements_set_version", None))
        submissions = [item async for item in db.traceability_submissions.find({})]
        deliveries = [item async for item in db.ifarlab_result_deliveries.find({})]
        verdicts = [item async for item in db.verification_verdicts.find({})]
        return calculate_requirement_coverage(requirement_set, submissions, deliveries, verdicts, **filters)

    async def snapshot(self, **filters) -> Dict[str, Any]:
        result = await self.calculate(**filters)
        db = await self.traceability_service._db()
        record = {**result, "snapshot_id": f"KPI34-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}"}
        await db.requirement_coverage_snapshots.insert_one(record)
        return record

    async def history(self, limit: int = 50) -> List[Dict[str, Any]]:
        db = await self.traceability_service._db()
        rows = [item async for item in db.requirement_coverage_snapshots.find({})]
        rows.sort(key=lambda item: item.get("evaluation_timestamp", ""), reverse=True)
        for row in rows[:limit]:
            row.pop("_id", None)
        return rows[:limit]
