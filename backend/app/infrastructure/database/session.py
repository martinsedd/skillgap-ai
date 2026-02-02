from contextlib import contextmanager
from typing import Generator

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import QueuePool

from app.core.config import settings
from app.infrastructure.logging import get_logger

logger = get_logger(__name__)

engine: Engine = create_engine(
    settings.DATABASE_URL,
    poolclass=QueuePool,
    pool_size=5,
    max_overflow=10,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=settings.LOG_LEVEL == "DEBUG",
)


@event.listens_for(engine, "connect")
def receive_connect(dpapi_conn: object, connection_record: object) -> None:
    logger.debug("database_connect", message="New database connection established")


@event.listens_for(engine, "checkout")
def receive_checkout(
    dbapi_conn: object, connection_record: object, connection_proxy: object
) -> None:
    logger.debug("connection_checkout", message="Connection checked out from pool")


SessionLocal: sessionmaker[Session] = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency for database sessions.
    Automatically handles commit/rollback and cleanup.
    """
    db: Session = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error("database_error", err=str(e), exc_info=True)
        raise
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[Session, None, None]:
    """
    Context manager for database sessions.
    Use this in non-FastAPI contexts
    """
    db: Session = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception as e:
        db.rollback()
        logger.error("database_error", error=str(e), exc_info=True)
        raise
    finally:
        db.close()


def init_db() -> None:
    from app.infrastructure.database.models import Base

    logger.info("database_init", message="Initializing database")
    Base.metadata.create_all(bind=engine)
    logger.info("database_init_complete", message="Database initialized")


def close_db() -> None:
    logger.info("database_shutdown", message="Closing database connections")
