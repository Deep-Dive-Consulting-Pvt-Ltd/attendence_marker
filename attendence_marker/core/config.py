import os
from dataclasses import dataclass


@dataclass
class AppConfig:
    host: str = os.getenv("APP_HOST", "0.0.0.0")
    port: int = int(os.getenv("APP_PORT", "8000"))
    debug: bool = os.getenv("APP_DEBUG", "false").lower() == "true"
    data_dir: str = os.getenv("DATA_DIR", "data")
    faces_dir: str = os.getenv("FACES_DIR", "data/faces")
    attendance_crops_dir: str = os.getenv("ATTENDANCE_CROPS_DIR", "data/attendance_crops")
    temp_dir: str = os.getenv("TEMP_DIR", "temp_uploads")
    default_threshold: float = float(os.getenv("DEFAULT_THRESHOLD", "0.3"))
    default_session: str = os.getenv("DEFAULT_SESSION", "2025-26")
    cors_origins: str = os.getenv("CORS_ORIGINS", "*")


@dataclass
class MongoConfig:
    uri: str = os.getenv("MONGODB_URI", "")
    database: str = os.getenv("MONGODB_DATABASE", "attendance_db")
    connect_timeout_ms: int = int(os.getenv("MONGODB_CONNECT_TIMEOUT_MS", "15000"))


app_config = AppConfig()
mongo_config = MongoConfig()
