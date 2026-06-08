import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from uuid import uuid4

from app.database.connection import Base
from app.models.db import Tenant, User, Document, Conversation, Message
from app.utils.security import hash_password, create_access_token
from app.database.rls import set_tenant_context


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_db():
    """Create an in-memory SQLite database for testing."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    AsyncSessionLocal = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with AsyncSessionLocal() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def tenant_a(test_db: AsyncSession):
    """Create test tenant A."""
    tenant = Tenant(
        id=uuid4(),
        name="Tenant A",
        api_key_hash="hash_a",
        vector_db_collection_name="documents_tenant_a",
        max_documents=1000,
    )
    test_db.add(tenant)
    await test_db.commit()
    await test_db.refresh(tenant)
    return tenant


@pytest.fixture
async def tenant_b(test_db: AsyncSession):
    """Create test tenant B."""
    tenant = Tenant(
        id=uuid4(),
        name="Tenant B",
        api_key_hash="hash_b",
        vector_db_collection_name="documents_tenant_b",
        max_documents=1000,
    )
    test_db.add(tenant)
    await test_db.commit()
    await test_db.refresh(tenant)
    return tenant


@pytest.fixture
async def user_a(test_db: AsyncSession, tenant_a):
    """Create test user for tenant A."""
    user = User(
        id=uuid4(),
        tenant_id=tenant_a.id,
        email="user_a@tenant-a.com",
        password_hash=hash_password("password123"),
        is_active=True,
        is_admin=True,
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest.fixture
async def user_b(test_db: AsyncSession, tenant_b):
    """Create test user for tenant B."""
    user = User(
        id=uuid4(),
        tenant_id=tenant_b.id,
        email="user_b@tenant-b.com",
        password_hash=hash_password("password123"),
        is_active=True,
        is_admin=True,
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest.fixture
async def token_a(user_a):
    """Create JWT token for user A."""
    return create_access_token(data={"sub": str(user_a.id), "tenant_id": str(user_a.tenant_id)})


@pytest.fixture
async def token_b(user_b):
    """Create JWT token for user B."""
    return create_access_token(data={"sub": str(user_b.id), "tenant_id": str(user_b.tenant_id)})
