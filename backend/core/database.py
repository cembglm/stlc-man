"""
database.py
-----------
MongoDB bağlantısını ve temel veritabanı işlemlerini yönetir.
Örneğin, koleksiyonlara erişim, CRUD işlemleri gibi fonksiyonları burada tanımlayabilirsiniz.
"""

import logging
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import MongoClient
from pymongo import ASCENDING
from core.settings import get_settings

# Logger settings
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

def get_db():
    """
    Returns a synchronous MongoDB database connection
    """
    try:
        logger.info("Connecting to MongoDB (sync)")
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)

        # Test the connection
        client.server_info()
        db = client[DATABASE_NAME]
        logger.info("MongoDB sync connection successful")
        return db
    except Exception as e:
        logger.error(f"MongoDB sync connection failed: {str(e)}")
        raise

_settings = get_settings()
MONGO_URI = _settings.mongo_uri
DATABASE_NAME = _settings.database_name

async def get_database():
    try:
        logger.info("Connecting to MongoDB (async)")
        client = AsyncIOMotorClient(
            MONGO_URI,
            serverSelectionTimeoutMS=5000
        )
        await client.list_database_names()
        db = client[DATABASE_NAME]
        logger.info("MongoDB async connection successful")
        return db
    except Exception as e:
        logger.error(f"MongoDB async connection failed: {str(e)}")
        raise


TRACEABILITY_UNIQUE_INDEXES = {
    "requirement_sets": [("requirements_set_version", ASCENDING)],
    "traceability_submissions": [("submission_id", ASCENDING)],
    "ifarlab_result_deliveries": [("payload.run_id", ASCENDING)],
    "verification_verdicts": [("verdict_id", ASCENDING)],
    "defects": [("defect_id", ASCENDING)],
    "patches": [("patch_id", ASCENDING)],
    "rc_reports": [("rc_id", ASCENDING)],
    "promotions": [("promotion_id", ASCENDING)],
    "review_queue": [("review_id", ASCENDING)],
    "review_decisions": [("review_id", ASCENDING)],
    "regression_campaigns": [("campaign_id", ASCENDING)],
    "regression_comparisons": [("comparison_id", ASCENDING)],
    "mutant_requests": [("mutant_id", ASCENDING)],
    "mutant_results": [("mutant_id", ASCENDING)],
    "test_regeneration_queue": [("routing_key", ASCENDING)],
    "infrastructure_notifications": [("routing_key", ASCENDING)],
}


async def ensure_traceability_indexes(db=None):
    """Create the immutable-record uniqueness boundary required by the contract."""
    database = db or await get_database()
    created = {}
    for collection_name, keys in TRACEABILITY_UNIQUE_INDEXES.items():
        created[collection_name] = await database[collection_name].create_index(
            keys, unique=True, name=f"uq_{collection_name}_identity"
        )
    created["ifarlab_result_delivery_hash"] = await database.ifarlab_result_deliveries.create_index(
        [("delivery_sha256", ASCENDING)], unique=True, name="uq_result_delivery_sha256"
    )
    created["defect_routing_key"] = await database.defects.create_index(
        [("routing_key", ASCENDING)], unique=True, sparse=True, name="uq_defect_routing_key"
    )
    created["review_routing_key"] = await database.review_queue.create_index(
        [("routing_key", ASCENDING)], unique=True, name="uq_review_routing_key"
    )
    return created
