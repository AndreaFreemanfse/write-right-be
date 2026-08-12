import os
import uuid

os.environ.setdefault("DATABASE_URL", "sqlite:///./test.db")
os.environ.setdefault("SUPABASE_JWKS_URL", "https://example.com/jwks")
os.environ.setdefault("API_KEY", "test-key")
os.environ.setdefault("BASE_URL", "https://example.com")
os.environ.setdefault("MODEL", "test-model")

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from auth import get_current_user
from database import Base, get_db
from main import app


TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

TestingSessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


@pytest.fixture(autouse=True)
def reset_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    yield

    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    db = TestingSessionLocal()

    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def test_user():
    return {
        "id": uuid.uuid4(),
        "email": "owner@example.com",
    }


@pytest.fixture
def other_user():
    return {
        "id": uuid.uuid4(),
        "email": "other@example.com",
    }


@pytest.fixture
def client(test_user):
    def override_get_db():
        db = TestingSessionLocal()

        try:
            yield db
        finally:
            db.close()

    async def override_get_current_user():
        return test_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = (
        override_get_current_user
    )

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()