from contextlib import asynccontextmanager
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers.attendance_router import router as attendance_router
from core.config import app_config
from core.logging import configure_logging, get_logger
from core.middleware import RequestContextMiddleware
from db.mongo import close_db, init_collections

configure_logging()
logger = get_logger(__name__)

os.makedirs(app_config.temp_dir, exist_ok=True)
os.makedirs(app_config.faces_dir, exist_ok=True)
os.makedirs(app_config.attendance_crops_dir, exist_ok=True)


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("initializing_mongo_collections")
    init_collections()
    yield
    close_db()
    logger.info("shutdown_completed")


app = FastAPI(
    title="Attendance Marker API",
    description="Production-grade face recognition attendance system using MongoDB Atlas + MVC",
    version="3.0.0",
    lifespan=lifespan,
)

origins = [o.strip() for o in app_config.cors_origins.split(",")] if app_config.cors_origins else ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RequestContextMiddleware)
app.include_router(attendance_router)
