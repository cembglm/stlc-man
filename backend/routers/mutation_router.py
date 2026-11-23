from fastapi import APIRouter, Depends, Header, HTTPException, Query

from core.auth import require_api_key
from mutation.adapters import adapter_registry
from mutation.execution import execution_adapter
from mutation.models import BaselineEvidence, CampaignConfigurationUpdate, CampaignCreate, ResultEvidence
from mutation.service import mutation_service


router = APIRouter(prefix="/api/mutations/v1", tags=["Mutation Testing"], dependencies=[Depends(require_api_key)])


def missing():
    raise HTTPException(404, detail="Mutation campaign not found")


@router.get("/adapters")
async def adapters():
    return {"language_adapters": [adapter.metadata() for adapter in adapter_registry.values()],
            "execution_adapter": execution_adapter.metadata()}


@router.get("/operators")
async def operators():
    return {"operators": [
        {"family": "AOR", "name": "Arithmetic operator replacement"},
        {"family": "ROR", "name": "Relational operator replacement"},
        {"family": "LOR", "name": "Logical operator replacement"},
        {"family": "CON", "name": "Boolean/conditional negation"},
    ]}


@router.post("/campaigns", status_code=201)
async def create_campaign(request: CampaignCreate, x_session_id: str = Header(default=None)):
    return await mutation_service.create_campaign(request, x_session_id)


@router.get("/campaigns")
async def list_campaigns(limit: int = Query(default=50, ge=1, le=200)):
    return {"campaigns": await mutation_service.list_campaigns(limit)}


@router.get("/campaigns/{campaign_id}")
async def campaign(campaign_id: str):
    return await mutation_service.get_campaign(campaign_id) or missing()


@router.get("/campaigns/{campaign_id}/status")
async def campaign_status(campaign_id: str):
    data = await mutation_service.get_campaign(campaign_id)
    if not data:
        return missing()
    return {key: data.get(key) for key in ("campaign_id", "status", "mutant_count", "cancel_requested", "updated_at")}


@router.put("/campaigns/{campaign_id}/configuration")
async def update_configuration(campaign_id: str, update: CampaignConfigurationUpdate):
    try:
        return await mutation_service.update_configuration(campaign_id, update) or missing()
    except ValueError as exc:
        raise HTTPException(409, detail=str(exc))


@router.post("/campaigns/{campaign_id}/generate")
async def generate(campaign_id: str):
    try:
        return await mutation_service.generate(campaign_id) or missing()
    except (SyntaxError, NotImplementedError) as exc:
        raise HTTPException(422, detail=str(exc))


@router.get("/campaigns/{campaign_id}/mutants")
async def mutants(campaign_id: str, family: str = None):
    if not await mutation_service.get_campaign(campaign_id):
        return missing()
    return {"mutants": await mutation_service.mutants(campaign_id, family)}


@router.get("/campaigns/{campaign_id}/preview")
async def preview(campaign_id: str, family: str = None):
    """Return immutable generated source and diffs without executing them."""
    if not await mutation_service.get_campaign(campaign_id):
        return missing()
    return {"campaign_id": campaign_id, "execution_performed": False,
            "mutants": await mutation_service.mutants(campaign_id, family)}


@router.post("/campaigns/{campaign_id}/baseline")
async def baseline(campaign_id: str):
    return await mutation_service.baseline(campaign_id) or missing()


@router.post("/campaigns/{campaign_id}/baseline/evidence")
async def ingest_baseline(campaign_id: str, evidence: BaselineEvidence):
    return await mutation_service.ingest_baseline(campaign_id, evidence) or missing()


@router.post("/campaigns/{campaign_id}/execute", status_code=202)
async def execute(campaign_id: str):
    return await mutation_service.execute(campaign_id) or missing()


@router.post("/campaigns/{campaign_id}/cancel")
async def cancel(campaign_id: str):
    if not await mutation_service.cancel(campaign_id):
        return missing()
    return {"campaign_id": campaign_id, "status": "cancelled"}


@router.get("/campaigns/{campaign_id}/results")
async def results(campaign_id: str):
    return {"results": await mutation_service.results(campaign_id)}


@router.post("/campaigns/{campaign_id}/results")
async def ingest_result(campaign_id: str, evidence: ResultEvidence):
    try:
        return await mutation_service.ingest_result(campaign_id, evidence) or missing()
    except KeyError:
        raise HTTPException(404, detail="Mutant not found in campaign")


@router.get("/campaigns/{campaign_id}/score")
async def score(campaign_id: str):
    return await mutation_service.score(campaign_id)


@router.get("/campaigns/{campaign_id}/evidence")
async def evidence(campaign_id: str):
    return {"events": await mutation_service.evidence(campaign_id)}


@router.get("/campaigns/{campaign_id}/report")
async def report(campaign_id: str):
    campaign_data = await mutation_service.get_campaign(campaign_id)
    if not campaign_data:
        return missing()
    campaign_data.pop("source", None)
    return {"schema_version": "1.0", "campaign": campaign_data,
            "score": await mutation_service.score(campaign_id),
            "results": await mutation_service.results(campaign_id),
            "evidence": await mutation_service.evidence(campaign_id),
            "statement": "Mutation outcomes are test-strength evidence, not requirement verification verdicts or KPI 3.4 status."}
