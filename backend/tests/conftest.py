from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.infrastructure.database.models import Base
from app.infrastructure.database.session import get_db
from app.main import app

TEST_DATABASE_URL = "sqlite:///./test.db"


@pytest.fixture(scope="session", autouse=True)
def patch_jsonb_for_sqlite() -> None:
    from sqlalchemy import JSON
    from sqlalchemy.dialects.postgresql import JSONB

    import app.infrastructure.database.models as models

    for attr_name in dir(models):
        attr = getattr(models, attr_name)
        if hasattr(attr, "__tablename__"):
            for column in attr.__table__.columns:
                if isinstance(column.type, JSONB):
                    column.type = JSON()


@pytest.fixture(scope="function")
def test_db_engine():
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def test_db_session(test_db_engine) -> Generator[Session, None, None]:
    TestSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_db_engine,
    )
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def client(test_db_session: Session) -> Generator[TestClient, None, None]:
    def override_get_db() -> Generator[Session, None, None]:
        try:
            yield test_db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def default_user(test_db_session: Session) -> str:
    from datetime import datetime, timezone

    from app.infrastructure.database.models import UserModel

    user: UserModel = UserModel(id="default-user", created_at=datetime.now(timezone.utc))
    test_db_session.add(user)
    test_db_session.commit()
    test_db_session.refresh(user)

    return str(user.id)
