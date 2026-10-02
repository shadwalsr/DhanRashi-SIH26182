import asyncio

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.security import get_password_hash
from app.db.base import Base
from app.db.models import Org, Role, User
from app.db.session import get_db
from app.domain.enums import UserRole
from app.main import app

# Test SQLite in-memory database
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(TEST_DB_URL, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False)


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session():
    """Provides a fresh isolated database schema for each test."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession):
    """FastAPI test client with DB dependency override."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def seeded_entities(db_session: AsyncSession):
    """Creates initial org, roles, and one test user per role."""
    org = Org(name="Test Cyber Unit", code="TEST-ORG")
    db_session.add(org)
    await db_session.flush()

    roles = {}
    for role_enum in UserRole:
        role = Role(name=role_enum.value, description=f"Test role {role_enum.value}")
        db_session.add(role)
        await db_session.flush()
        roles[role_enum.value] = role

    users = {}
    for role_name, role_obj in roles.items():
        user = User(
            email=f"{role_name.lower()}@test.internal",
            hashed_password=get_password_hash("password123"),
            full_name=f"Test {role_name}",
            role_id=role_obj.id,
            org_id=org.id,
            is_active=True,
        )
        db_session.add(user)
        await db_session.flush()
        users[role_name] = user

    await db_session.commit()
    return {"org": org, "roles": roles, "users": users}
