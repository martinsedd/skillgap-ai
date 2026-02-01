from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.infrastructure.logging import get_logger, setup_logging

setup_logging(settings.LOG_LEVEL)
logger = get_logger(__name__)

app = FastAPI(
    title="SkillGap API",
    description="AI-powered job search assistant",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    # HACK: "*" for development only
    allow_origins=["*"],
    # allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@asynccontextmanager
async def lifespan(app):
    logger.info("application_startup", message="SkillGap API starting up")
    yield
    logger.info("application_shutdown", message="SkillGap API shutting donw")


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "skillgap-ai"}
