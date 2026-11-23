"""Versioned ASRLab/IFARLAB export, ingestion, and traceability APIs."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import base64
import binascii
import re

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from core.auth import require_api_key
from core.database import get_database
from models.ifarlab_lifecycle import DefectRecord, PatchRecord, PromotionRecord, RCReport
from models.traceability import CodeQuality, GenerationProvenance, IFARLABResult, ManifestSUT, ManifestTest, RequirementSet, SubmissionManifest
from services.traceability_contract import contract_document, contract_sha256, sha256_bytes, validate_manifest_mapping
from services.traceability_service import traceability_service
from services.ifarlab_package_service import ResultPackageError, read_result_package
from services.requirement_coverage_service import RequirementCoverageService
from services.lifecycle_service import insert_immutable, save_patch, save_promotion, save_rc_report
from services.sut_package_service import SUTPackageError, persist_sut_package


router = APIRouter(prefix="/api/integrations/ifarlab/v1", tags=["ASRLab-IFARLAB traceability"], dependencies=[Depends(require_api_key)])
coverage_service = RequirementCoverageService(traceability_service)


class SubmissionCreate(BaseModel):
    code: str = Field(..., min_length=1)
    requirements_set_version: str
    generation: GenerationProvenance
    code_quality: CodeQuality = Field(default_factory=CodeQuality)
    tests: List[ManifestTest]
    sut: Optional[ManifestSUT] = None
    submission_id: Optional[str] = None
    revision: int = Field(1, ge=1)
    project_id: Optional[str] = None
    session_id: Optional[str] = None


class SUTPackageImport(BaseModel):
    source_archive_base64: str = Field(..., min_length=1)
    sut_release: Dict[str, Any]
    requirements: Dict[str, Any]


@router.get("/contract")
async def get_contract():
    return {**contract_document(), "contract_sha256": contract_sha256()}


@router.post("/requirements", status_code=status.HTTP_201_CREATED)
async def import_requirements(payload: RequirementSet):
    try:
        return await traceability_service.save_requirement_set(payload)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc


@router.post("/sut-releases/import", status_code=status.HTTP_201_CREATED)
async def import_sut_release(payload: SUTPackageImport):
    """Import the three-part IFARLAB package without extracting its source archive."""
    try:
        archive = base64.b64decode(payload.source_archive_base64, validate=True)
        db = await get_database()
        record = await persist_sut_package(
            db, archive, payload.sut_release, payload.requirements
        )
    except (binascii.Error, ValueError, SUTPackageError) as exc:
        raise HTTPException(422, str(exc)) from exc
    return {key: value for key, value in record.items() if key not in {"_id", "source_archive"}}


@router.post("/defects", status_code=status.HTTP_201_CREATED)
async def create_defect(payload: DefectRecord):
    db = await get_database()
    try:
        return await insert_immutable(
            db.defects, {"defect_id": payload.defect_id}, payload.model_dump(mode="json")
        )
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc


@router.post("/patches", status_code=status.HTTP_201_CREATED)
async def create_patch(payload: PatchRecord):
    db = await get_database()
    try:
        return await save_patch(db, payload)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc


@router.post("/release-candidates", status_code=status.HTTP_201_CREATED)
async def create_release_candidate(payload: RCReport):
    db = await get_database()
    try:
        return await save_rc_report(db, payload)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc


@router.post("/promotions", status_code=status.HTTP_201_CREATED)
async def create_promotion(payload: PromotionRecord):
    db = await get_database()
    try:
        return await save_promotion(db, payload)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc


@router.get("/requirements.json")
async def export_requirements(version: Optional[str] = None):
    result = await traceability_service.current_requirement_set(version)
    if not result:
        raise HTTPException(404, "Requirement set not found")
    return {key: value for key, value in result.items() if key in {"schema_version", "requirements_set_version", "requirements"}}


@router.post("/submissions", status_code=status.HTTP_201_CREATED)
async def create_submission(payload: SubmissionCreate):
    requirement_set = await traceability_service.current_requirement_set(payload.requirements_set_version)
    if not requirement_set:
        raise HTTPException(422, "Referenced requirement set version does not exist")
    qcr_flow = all(item["id"].startswith("QCR-") for item in requirement_set["requirements"])
    if qcr_flow:
        quality = payload.code_quality
        if any(value.lower() != "pass" for value in (quality.validator, quality.lint, quality.verdict)):
            raise HTTPException(422, "Validator, lint, and aggregate code-quality verdict must all pass")
        if payload.sut is None:
            raise HTTPException(422, "QCR submissions require an immutable SUT version reference")
        db = await get_database()
        sut = await db.sut_releases.find_one({
            "sut_id": payload.sut.sut_id,
            "version": payload.sut.version,
            "source_sha256": payload.sut.source_sha256,
        })
        if not sut:
            raise HTTPException(422, "Referenced SUT release does not exist or its hash differs")
        req_by_id = {item["id"]: item for item in requirement_set["requirements"]}
        for test in payload.tests:
            if not test.requirements:
                raise HTTPException(422, f"{test.test_case_id} is not linked to a QCR")
            if test.test_case_id.startswith("INSP_") and not (
                test.scenario_id and re.fullmatch(r"SC-[0-9]{3}", test.scenario_id)
            ):
                raise HTTPException(422, f"{test.test_case_id} requires an SC-NNN scenario_id")
            for requirement_id in test.requirements:
                requirement = req_by_id.get(requirement_id)
                if not requirement:
                    continue
                for field_name in ("expected_outcome", "expected_reason"):
                    expected = requirement.get(field_name)
                    if expected is not None and getattr(test, field_name) != expected:
                        raise HTTPException(422, f"{test.test_case_id}.{field_name} must equal {requirement_id}")
                expected_oracle = requirement.get("oracle")
                if expected_oracle is not None and test.oracle != expected_oracle:
                    raise HTTPException(422, f"{test.test_case_id}.oracle must equal {requirement_id}")
    elif payload.code_quality.validator.lower() == "fail":
        raise HTTPException(422, "Validator failure prevents submission to IFARLAB")
    code_hash = sha256_bytes(payload.code.encode("utf-8"))
    submission_id = payload.submission_id or await traceability_service.next_submission_id()
    manifest = SubmissionManifest(
        submission_id=submission_id, revision=payload.revision, code_sha256=code_hash,
        requirements_set_version=payload.requirements_set_version, contract_sha256=contract_sha256(),
        generation=payload.generation, code_quality=payload.code_quality, tests=payload.tests,
        sut=payload.sut,
        project_id=payload.project_id, session_id=payload.session_id,
    )
    try:
        validate_manifest_mapping(
            payload.code, manifest,
            [item["id"] for item in requirement_set["requirements"]],
            [item.test_case_id for item in payload.tests],
        )
        return await traceability_service.save_submission(manifest, payload.code)
    except (SyntaxError, ValueError) as exc:
        code = 409 if "already exists" in str(exc) else 422
        raise HTTPException(code, str(exc)) from exc


@router.get("/submissions/{submission_id}/manifest.json")
async def export_manifest(submission_id: str):
    submission = await traceability_service.submission(submission_id)
    if not submission:
        raise HTTPException(404, "Submission not found")
    return submission["manifest"]


@router.get("/submissions/{submission_id}/test.py")
async def export_test_code(submission_id: str):
    submission = await traceability_service.submission(submission_id)
    if not submission:
        raise HTTPException(404, "Submission not found")
    return {"submission_id": submission_id, "code": submission["code"], "code_sha256": submission["manifest"]["code_sha256"]}


@router.post("/results", status_code=status.HTTP_202_ACCEPTED)
async def ingest_result(payload: IFARLABResult):
    return await traceability_service.ingest_result(payload)


@router.post("/inbox/{package_name}/import", status_code=status.HTTP_202_ACCEPTED)
async def import_result_package(package_name: str):
    """Import a package already delivered by the restricted SSH inbox account."""
    try:
        payload = read_result_package(package_name)
    except FileNotFoundError as exc:
        raise HTTPException(404, "Result package not found in the configured inbox") from exc
    except ResultPackageError as exc:
        raise HTTPException(422, str(exc)) from exc
    result = await traceability_service.ingest_result(payload)
    return {"package_name": package_name, **result}


@router.get("/traceability")
async def traceability(search: Optional[str] = Query(None), verdict: Optional[str] = Query(None)):
    return await traceability_service.dashboard(search, verdict)


@router.get("/report")
async def traceability_report():
    """Backward-compatible general traceability report."""
    return await traceability_service.dashboard()


@router.get("/coverage/report")
async def kpi_3_4_report(
    requirements_set_version: Optional[str] = None, project_id: Optional[str] = None,
    session_id: Optional[str] = None, environment_id: Optional[str] = None,
    digital_twin_id: Optional[str] = None,
):
    """Machine-readable KPI 3.4 report from the dashboard's calculation service."""
    return await coverage_service.calculate(
        requirements_set_version=requirements_set_version, project_id=project_id,
        session_id=session_id, environment_id=environment_id, digital_twin_id=digital_twin_id,
    )


@router.get("/coverage")
async def requirement_coverage(
    requirements_set_version: Optional[str] = None,
    project_id: Optional[str] = None,
    session_id: Optional[str] = None,
    environment_id: Optional[str] = None,
    digital_twin_id: Optional[str] = None,
    requirement_type: Optional[str] = Query(None, pattern="^(functional|non_functional|unclassified)$"),
    coverage_stage: Optional[str] = Query(None, pattern="^(unmapped|mapped|generated|executable|executed_dt|verified_dt)$"),
    verification_state: Optional[str] = Query(None, pattern="^(PASS|FAIL|NOT_VERIFIED|NOT_COVERED|STALE)$"),
):
    result = await coverage_service.calculate(
        requirements_set_version=requirements_set_version, project_id=project_id,
        session_id=session_id, environment_id=environment_id, digital_twin_id=digital_twin_id,
    )
    if requirement_type or coverage_stage or verification_state:
        result["requirements"] = [
            item for item in result["requirements"]
            if (not requirement_type or item.get("type") == requirement_type)
            and (not coverage_stage or item.get("coverage_stage") == coverage_stage)
            and (not verification_state or item.get("verification_state") == verification_state)
        ]
    return result


@router.get("/coverage/functional")
async def functional_coverage(requirements_set_version: Optional[str] = None, environment_id: Optional[str] = None):
    result = await coverage_service.calculate(requirements_set_version=requirements_set_version, environment_id=environment_id)
    return {"scope": result["scope"], "evaluation_timestamp": result["evaluation_timestamp"], "executed_dt": result["kpi"]["functional"], "verified_dt": result["verified"]["functional"]}


@router.get("/coverage/non-functional")
async def non_functional_coverage(requirements_set_version: Optional[str] = None, environment_id: Optional[str] = None):
    result = await coverage_service.calculate(requirements_set_version=requirements_set_version, environment_id=environment_id)
    return {"scope": result["scope"], "evaluation_timestamp": result["evaluation_timestamp"], "executed_dt": result["kpi"]["non_functional"], "verified_dt": result["verified"]["non_functional"]}


@router.get("/coverage/requirements/{requirement_id}")
async def requirement_coverage_detail(requirement_id: str, requirements_set_version: Optional[str] = None):
    result = await coverage_service.calculate(requirements_set_version=requirements_set_version)
    match = next((item for item in result["requirements"] if item["id"] == requirement_id), None)
    if not match:
        raise HTTPException(404, "Requirement not found in the selected coverage scope")
    return {"scope": result["scope"], "evaluation_timestamp": result["evaluation_timestamp"], "requirement": match}


@router.get("/coverage/gaps/{category}")
async def coverage_gaps(
    category: str,
    requirements_set_version: Optional[str] = None,
    environment_id: Optional[str] = None,
):
    if category not in {"uncovered", "generated_unexecuted", "failed_inconclusive", "stale"}:
        raise HTTPException(422, "Unknown gap category")
    result = await coverage_service.calculate(requirements_set_version=requirements_set_version, environment_id=environment_id)
    predicates = {
        "uncovered": lambda item: not item["executed_dt"],
        "generated_unexecuted": lambda item: item["generated"] and not item["executed_dt"],
        "failed_inconclusive": lambda item: item["verification_state"] in {"FAIL", "NOT_VERIFIED"},
        "stale": lambda item: item["verification_state"] == "STALE" or any(chain["stale"] for chain in item["traceability_chains"]),
    }
    rows = [item for item in result["requirements"] if predicates[category](item)]
    return {"scope": result["scope"], "evaluation_timestamp": result["evaluation_timestamp"], "category": category, "count": len(rows), "requirements": rows}


@router.post("/coverage/snapshots", status_code=status.HTTP_201_CREATED)
async def create_coverage_snapshot(requirements_set_version: Optional[str] = None, environment_id: Optional[str] = None):
    return await coverage_service.snapshot(requirements_set_version=requirements_set_version, environment_id=environment_id)


@router.get("/coverage/snapshots")
async def coverage_snapshot_history(limit: int = Query(50, ge=1, le=500)):
    return {"snapshots": await coverage_service.history(limit), "limit": limit}
