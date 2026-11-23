import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Optional

from core.database import get_database
from .adapters import adapter_registry
from .evaluator import calculate_score, classify_mutant
from .execution import execution_adapter


def _now():
    return datetime.now(timezone.utc).isoformat()


def _dump(model):
    return model.model_dump() if hasattr(model, "model_dump") else model.dict()


class MutationService:
    async def _db(self):
        return await get_database()

    async def _event(self, db, campaign, event_type, payload=None):
        await db.traceability_events.insert_one({
            "event_id": f"evt_{uuid.uuid4().hex}", "event_type": event_type,
            "entity_type": "mutation_campaign", "entity_id": campaign["campaign_id"],
            "session_id": campaign.get("session_id"), "requirement_refs": campaign.get("requirement_refs", []),
            "test_refs": campaign.get("test_refs", []), "source_hash": campaign["source_hash"],
            "payload": payload or {}, "occurred_at": _now(),
            "mutation_verdict_is_requirement_verdict": False,
        })

    async def create_campaign(self, request, session_id: Optional[str] = None):
        data = _dump(request)
        source_hash = hashlib.sha256(data["source"].encode()).hexdigest()
        config_hash = hashlib.sha256(json.dumps({k: v for k, v in data.items() if k != "name"}, sort_keys=True).encode()).hexdigest()
        campaign = {**data, "campaign_id": f"mc_{uuid.uuid4().hex}", "session_id": session_id,
                    "source_hash": source_hash, "configuration_hash": config_hash, "status": "draft",
                    "baseline": None, "created_at": _now(), "updated_at": _now(), "cancel_requested": False}
        db = await self._db()
        await db.mutation_campaigns.insert_one(campaign.copy())
        await self._event(db, campaign, "mutation.campaign.created")
        campaign.pop("_id", None)
        return campaign

    async def list_campaigns(self, limit=50):
        db = await self._db()
        rows = await db.mutation_campaigns.find({}, {"_id": 0, "source": 0}).sort("created_at", -1).limit(limit).to_list(limit)
        return rows

    async def get_campaign(self, campaign_id):
        db = await self._db()
        return await db.mutation_campaigns.find_one({"campaign_id": campaign_id}, {"_id": 0})

    async def update_configuration(self, campaign_id, update):
        db = await self._db()
        campaign = await db.mutation_campaigns.find_one({"campaign_id": campaign_id}, {"_id": 0})
        if not campaign:
            return None
        if campaign.get("status") != "draft":
            raise ValueError("configuration is immutable after mutant generation")
        changes = {key: value for key, value in _dump(update).items() if value is not None}
        changes["updated_at"] = _now()
        await db.mutation_campaigns.update_one({"campaign_id": campaign_id}, {"$set": changes})
        campaign.update(changes)
        return campaign

    async def generate(self, campaign_id):
        db = await self._db()
        campaign = await db.mutation_campaigns.find_one({"campaign_id": campaign_id}, {"_id": 0})
        if not campaign:
            return None
        adapter = adapter_registry[campaign["language"]]
        mutants = adapter.generate(campaign["source"], campaign["source_path"], campaign["operator_families"],
                                   campaign.get("max_mutants"), campaign.get("seed"), campaign.get("function_scope"))
        for mutant in mutants:
            document = {**mutant, "campaign_id": campaign_id, "created_at": _now()}
            await db.mutation_mutants.update_one({"campaign_id": campaign_id, "mutant_id": mutant["mutant_id"]},
                                                 {"$setOnInsert": document}, upsert=True)
        await db.mutation_campaigns.update_one({"campaign_id": campaign_id},
                                               {"$set": {"status": "generated", "mutant_count": len(mutants), "updated_at": _now()}})
        await self._event(db, campaign, "mutation.mutants.generated", {"mutant_count": len(mutants)})
        return {"campaign_id": campaign_id, "mutant_count": len(mutants), "mutants": mutants}

    async def mutants(self, campaign_id, family=None, limit=5000):
        db = await self._db()
        query = {"campaign_id": campaign_id}
        if family:
            query["family"] = family
        return await db.mutation_mutants.find(query, {"_id": 0}).sort([("line", 1), ("column", 1), ("family", 1)]).limit(limit).to_list(limit)

    async def baseline(self, campaign_id):
        db = await self._db()
        campaign = await db.mutation_campaigns.find_one({"campaign_id": campaign_id}, {"_id": 0})
        if not campaign:
            return None
        result = await execution_adapter.run_baseline(campaign)
        status = "ready" if result.get("status") == "completed" else "baseline_unavailable"
        await db.mutation_campaigns.update_one({"campaign_id": campaign_id}, {"$set": {"baseline": result, "status": status, "updated_at": _now()}})
        await self._event(db, campaign, "mutation.baseline.recorded", {"status": result["status"]})
        return result

    async def ingest_baseline(self, campaign_id, evidence):
        db = await self._db()
        campaign = await db.mutation_campaigns.find_one({"campaign_id": campaign_id}, {"_id": 0})
        if not campaign:
            return None
        data = _dump(evidence)
        from .evaluator import baseline_is_valid
        status = "ready" if baseline_is_valid(data) else "baseline_unavailable"
        await db.mutation_campaigns.update_one({"campaign_id": campaign_id}, {"$set": {"baseline": data, "status": status, "updated_at": _now()}})
        await self._event(db, campaign, "mutation.baseline.evidence_ingested", {"valid": status == "ready"})
        return {"baseline": data, "campaign_status": status, "valid": status == "ready"}

    async def execute(self, campaign_id):
        db = await self._db()
        campaign = await db.mutation_campaigns.find_one({"campaign_id": campaign_id}, {"_id": 0})
        if not campaign:
            return None
        mutants = await self.mutants(campaign_id)
        results = await execution_adapter.run_mutants(mutants, campaign)
        for result in results:
            result.update({"campaign_id": campaign_id, "outcome": "not_executed", "updated_at": _now()})
            await db.mutation_results.update_one({"campaign_id": campaign_id, "mutant_id": result["mutant_id"]}, {"$set": result}, upsert=True)
        await db.mutation_campaigns.update_one({"campaign_id": campaign_id}, {"$set": {"status": "baseline_unavailable", "updated_at": _now()}})
        return {"campaign_id": campaign_id, "status": "execution_unavailable", "results": results,
                "execution_adapter": execution_adapter.metadata()}

    async def ingest_result(self, campaign_id, evidence):
        db = await self._db()
        campaign = await db.mutation_campaigns.find_one({"campaign_id": campaign_id}, {"_id": 0})
        if not campaign:
            return None
        data = _dump(evidence)
        mutant = await db.mutation_mutants.find_one({"campaign_id": campaign_id, "mutant_id": data["mutant_id"]}, {"_id": 0})
        if not mutant:
            raise KeyError(data["mutant_id"])
        outcome = classify_mutant(campaign.get("baseline") or {}, data)
        reasons = {
            "killed": "At least one baseline-passing test failed for this mutant.",
            "survived": "All recorded baseline tests completed with unchanged passing outcomes.",
            "invalid": "The execution provider reported the mutant as invalid.",
            "timeout": "The execution provider reported a timeout.",
            "execution_error": "The execution provider reported an infrastructure or execution error.",
            "equivalent": "Equivalence was explicitly confirmed by independent review.",
            "undetermined": "Evidence was insufficient or the baseline was not valid.",
            "not_executed": "No mutant execution evidence was supplied.",
        }
        record = {**data, **{key: mutant.get(key) for key in ("family", "source_path", "function", "line")},
                  "campaign_id": campaign_id, "outcome": outcome, "reason": reasons[outcome], "updated_at": _now()}
        record["evidence_hash"] = hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()
        await db.mutation_results.update_one({"campaign_id": campaign_id, "mutant_id": data["mutant_id"]}, {"$set": record}, upsert=True)
        await self._event(db, campaign, "mutation.result.ingested", {"mutant_id": data["mutant_id"], "outcome": outcome})
        return record

    async def results(self, campaign_id):
        db = await self._db()
        return await db.mutation_results.find({"campaign_id": campaign_id}, {"_id": 0}).sort("mutant_id", 1).to_list(5000)

    async def score(self, campaign_id):
        return calculate_score(await self.results(campaign_id))

    async def evidence(self, campaign_id):
        db = await self._db()
        return await db.traceability_events.find({"entity_type": "mutation_campaign", "entity_id": campaign_id}, {"_id": 0}).sort("occurred_at", 1).to_list(5000)

    async def cancel(self, campaign_id):
        db = await self._db()
        result = await db.mutation_campaigns.update_one({"campaign_id": campaign_id}, {"$set": {"status": "cancelled", "cancel_requested": True, "updated_at": _now()}})
        return bool(result.matched_count)


mutation_service = MutationService()
