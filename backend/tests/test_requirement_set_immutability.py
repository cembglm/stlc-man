import pytest

from models.traceability import RequirementSet
from services.traceability_service import TraceabilityService


class Collection:
    def __init__(self): self.rows = []
    async def find_one(self, query, **_kwargs):
        return next((row for row in self.rows if all(row.get(k) == v for k, v in query.items())), None)
    async def insert_one(self, value): self.rows.append(dict(value))
    async def update_many(self, query, update):
        for row in self.rows:
            if all(row.get(k) == v for k, v in query.items()): row.update(update.get("$set", {}))


class DB:
    def __init__(self):
        self.requirement_sets = Collection()
        self.traceability_events = Collection()


def req(text):
    return RequirementSet(
        requirements_set_version="QCR-2026-11-19",
        requirements=[{"id": "QCR-001", "version": "1.0", "type": "functional", "text": text}],
    )


def drive(coroutine):
    try: coroutine.send(None)
    except StopIteration as done: return done.value
    raise AssertionError("unexpected await")


def test_same_requirement_set_version_cannot_be_reused_for_new_content():
    db = DB()
    service = TraceabilityService()
    async def get_db(): return db
    service._db = get_db
    drive(service.save_requirement_set(req("original")))
    with pytest.raises(ValueError, match="already exists"):
        drive(service.save_requirement_set(req("original")))
    with pytest.raises(ValueError, match="already exists with different content"):
        drive(service.save_requirement_set(req("changed")))
    assert len(db.requirement_sets.rows) == 1
