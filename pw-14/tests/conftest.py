import asyncio
import logging
import os
from pathlib import Path
from fastapi import Request, Response

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

# Tell application settings that pytest is running before importing main.
# Route modules create limiter objects at import time, so this must happen first.
os.environ["TESTING"] = "True"

from main import app
from src.entity.models import Base, User
from src.database.db import get_db
from src.services.auth import auth_service

logger = logging.getLogger()

# Store the test database next to this conftest.py file so its location does
# not depend on the directory from which pytest is started.
BASE_DIR = Path(__file__).resolve().parent
SQLALCHEMY_DATABASE_URL = f"sqlite+aiosqlite:///{BASE_DIR / 'test.db'}"

# Async SQLite engine used only by tests.
# StaticPool keeps the same connection available during the test session.
engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

# Factory for SQLAlchemy async sessions that will be injected into FastAPI.
TestingSessionLocal = async_sessionmaker(
    autocommit=False, autoflush=False, expire_on_commit=False, bind=engine
)

# Default user created before tests run. Tests can use it for login/token checks.
test_user = {
    "username": "test_user",
    "email": "test_user@mail.com",
    "password": "1234567890",
}


@pytest.fixture(autouse=True)
def disable_rate_limiter(monkeypatch):
    """Disable FastAPI rate limiting in endpoint tests."""

    async def mock_rate_limiter_call(
        self,
        request: Request,
        response: Response,
    ) -> None:
        return None

    monkeypatch.setattr(RateLimiter, "__call__", mock_rate_limiter_call)


@pytest.fixture(scope="module", autouse=True)
def init_models_wrap():
    # Recreate all tables and insert a confirmed admin user once per test module.
    async def init_models():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        async with TestingSessionLocal() as session:
            hash_password = auth_service.get_password_hash(test_user["password"])
            current_user = User(
                username=test_user["username"],
                email=test_user["email"],
                password=hash_password,
                confirmed=True,
                role="admin",
            )
            session.add(current_user)
            await session.commit()

    asyncio.run(init_models())


@pytest.fixture(scope="module")
def client():
    # Replace the real application database dependency with the test session.
    async def override_get_db():
        session = TestingSessionLocal()
        try:
            yield session
        except Exception as err:
            logger.error(err)
            await session.rollback()
            raise
        finally:
            await session.close()

    app.dependency_overrides[get_db] = override_get_db

    yield TestClient(app)

    # Remove test overrides so they do not leak into other test modules.
    app.dependency_overrides.clear()


@pytest_asyncio.fixture()
def get_token() -> str:
    """Generate an access token for the default test user."""
    token = auth_service.create_access_token(payload={"sub": test_user["email"]})
    return token
