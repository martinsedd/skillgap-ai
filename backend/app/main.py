from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.middleware import LoggingMiddleware
from app.api.routes import jobs, resume
from app.core.config import settings
from app.infrastructure.logging import get_logger, setup_logging
from app.infrastructure.scheduler.scheduler import shutdown_scheduler, start_scheduler

# INFO: Setup logging
setup_logging(settings.LOG_LEVEL)
logger = get_logger(__name__)

# INFO: Create FastAPI app
app = FastAPI(
    title="SkillGap API",
    description="AI-powered job search assistant",
    version="0.1.0",
)

# INFO: Add middlewares

app.add_middleware(LoggingMiddleware)

app.add_middleware(
    CORSMiddleware,
    # HACK: "*" for development only
    allow_origins=["*"],
    # allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# INFO: Lifespan handling
@asynccontextmanager
async def lifespan(app):
    logger.info("application_startup", message="SkillGap API starting up")

    start_scheduler()
    logger.info("scheduler_started")

    yield

    shutdown_scheduler()
    logger.info("application_shutdown", message="SkillGap API shutting donw")


# INFO: Register routes
app.include_router(resume.router)
app.include_router(jobs.router)


# INFO: Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "skillgap-ai"}
