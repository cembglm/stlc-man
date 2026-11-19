"""Versioned ASRLab/IFARLAB export, ingestion, and traceability APIs."""

from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from core.auth import require_api_key
from models.traceability import CodeQuality, GenerationProvenance, IFARLABResult, ManifestTest, RequirementSet, SubmissionManifest
from services.traceability_contract import contract_document, contract_sha256, sha256_bytes, validate_manifest_mapping
from services.traceability_service import traceability_service
from services.ifarlab_package_service import ResultPackageError, read_result_package


router = APIRouter(prefix="/api/integrations/ifarlab/v1", tags=["ASRLab-IFARLAB traceability"], dependencies=[Depends(require_api_key)])


class SubmissionCreate(BaseModel):
    code: str = Field(..., min_length=1)
    requirements_set_version: str
    generation: GenerationProvenance
    code_quality: CodeQuality = Field(default_factory=CodeQuality)
    tests: List[ManifestTest]
    submission_id: Optional[str] = None
    revision: int = Field(1, ge=1)


@router.get("/contract")
async def get_contract():
    return {**contract_document(), "contract_sha256": contract_sha256()}


@router.post("/requirements", status_code=status.HTTP_201_CREATED)
async def import_requirements(payload: RequirementSet):
    return await traceability_service.save_requirement_set(payload)


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
    if payload.code_quality.validator.lower() == "fail":
        raise HTTPException(422, "Validator failure prevents submission to IFARLAB")
    code_hash = sha256_bytes(payload.code.encode("utf-8"))
    submission_id = payload.submission_id or await traceability_service.next_submission_id()
    manifest = SubmissionManifest(
        submission_id=submission_id, revision=payload.revision, code_sha256=code_hash,
        requirements_set_version=payload.requirements_set_version, contract_sha256=contract_sha256(),
        generation=payload.generation, code_quality=payload.code_quality, tests=payload.tests,
    )
    try:
        validate_manifest_mapping(
            payload.code, manifest,
            [item["id"] for item in requirement_set["requirements"]],
            [item.test_case_id for item in payload.tests],
        )
        return await traceability_service.save_submission(manifest, payload.code)
    except (SyntaxError, ValueError) as exc:
        raise HTTPException(422, str(exc)) from exc


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
    """Machine-readable reporting source for existing report/export workflows."""
    return await traceability_service.dashboard()
