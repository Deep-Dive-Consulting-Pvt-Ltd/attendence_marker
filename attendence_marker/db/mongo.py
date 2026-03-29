from datetime import datetime
from typing import Optional

from pymongo import ASCENDING, MongoClient
from pymongo.database import Database

from core.config import mongo_config
from core.logging import get_logger

logger = get_logger(__name__)
_client: Optional[MongoClient] = None
_db: Optional[Database] = None


def get_db() -> Database:
    global _client, _db
    if _db is not None:
        return _db
    if not mongo_config.uri:
        raise RuntimeError("MONGODB_URI is not configured")
    _client = MongoClient(mongo_config.uri, serverSelectionTimeoutMS=mongo_config.connect_timeout_ms)
    _db = _client[mongo_config.database]
    _client.admin.command("ping")
    logger.info("mongo_connected", extra={"extra_fields": {"database": mongo_config.database}})
    return _db


def close_db() -> None:
    global _client, _db
    if _client is not None:
        _client.close()
        logger.info("mongo_connection_closed")
    _client = None
    _db = None


def init_collections() -> None:
    db = get_db()
    db.students.create_index(
        [("school_name", ASCENDING), ("roll_no", ASCENDING), ("session", ASCENDING)],
        unique=True,
        name="students_identity_unique",
    )
    db.students.create_index(
        [("school_name", ASCENDING), ("session", ASCENDING), ("class_name", ASCENDING), ("section", ASCENDING)],
        name="students_lookup_idx",
    )
    db.attendance.create_index(
        [("school_name", ASCENDING), ("session", ASCENDING), ("class_name", ASCENDING), ("section", ASCENDING), ("date", ASCENDING)],
        name="attendance_lookup_idx",
    )
    db.change_logs.create_index([("timestamp", ASCENDING)], name="change_logs_timestamp_idx")

    # Atlas Search index must exist in cluster; storing desired definition for ops visibility.
    db.system_metadata.update_one(
        {"_id": "vector_index_manifest"},
        {
            "$set": {
                "collection": "students",
                "index_name": "students_embedding_vector_index",
                "field": "embedding",
                "dimensions": 512,
                "similarity": "cosine",
                "updated_at": datetime.utcnow(),
            }
        },
        upsert=True,
    )
    logger.info("mongo_collections_initialized")
