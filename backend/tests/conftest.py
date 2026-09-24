"""Shared pytest fixtures.

Tests run against an in-memory SQLite database via aiosqlite rather than
MariaDB, so they're fast and require no external services. The ORM
models/mappers are database-agnostic enough that this is a faithful
enough substitute for unit/integration-level API tests; true MariaDB
compatibility (e.g. real migrations) is exercised by `alembic upgrade
head` in CI/deployment instead.
"""
from __future__ import annotations

import asyncio
import os
import tempfile
from typing import AsyncIterator

# Route file uploads (attachments, logo) to an isolated temp directory
# rather than the default "./uploads" relative to the backend package -
# must happen before anything imports app.infrastructure.config.settings,
# since get_settings() is lru_cached on first call.
os.environ.setdefault("UPLOAD_DIR", tempfile.mkdtemp(prefix="asset-inventory-test-uploads-"))

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.infrastructure.database.base import Base
from app.infrastructure.database import models  # noqa: F401 registers all tables
from app.infrastructure.database.unit_of_work import SqlAlchemyUnitOfWork

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest_asyncio.fixture
async def session() -> AsyncIterator[AsyncSession]:
    engine = create_async_engine(TEST_DATABASE_URL, future=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with factory() as s:
        yield s

    await engine.dispose()


@pytest_asyncio.fixture
async def uow(session: AsyncSession) -> SqlAlchemyUnitOfWork:
    return SqlAlchemyUnitOfWork(session)


@pytest_asyncio.fixture
async def app_client(session: AsyncSession) -> AsyncIterator[AsyncClient]:
    """An httpx AsyncClient bound to the FastAPI app, with the DB session
    dependency overridden to use the in-memory SQLite fixture."""
    from app.api.deps import get_uow
    from app.infrastructure.database.session import get_session
    import app.main as main_module

    async def _override_get_session():
        yield session

    async def _override_get_uow():
        yield SqlAlchemyUnitOfWork(session)

    main_module.app.dependency_overrides[get_session] = _override_get_session
    main_module.app.dependency_overrides[get_uow] = _override_get_uow

    transport = ASGITransport(app=main_module.app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    main_module.app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def authed_client(app_client, session) -> AsyncIterator[AsyncClient]:
    """An app_client already logged in as an Admin user - the common case
    for tests that just need to exercise an authenticated endpoint rather
    than test role enforcement itself."""
    from app.infrastructure.database.models.user import UserModel
    from app.infrastructure.security.password_hasher import BcryptPasswordHasher

    session.add(
        UserModel(
            username="admin",
            hashed_password=BcryptPasswordHasher().hash("ChangeMe123!"),
            role="Admin",
            is_active=True,
        )
    )
    await session.commit()

    resp = await app_client.post("/api/v1/auth/login", json={"username": "admin", "password": "ChangeMe123!"})
    assert resp.status_code == 200, resp.text
    token = resp.json()["access_token"]
    app_client.headers["Authorization"] = f"Bearer {token}"
    yield app_client
