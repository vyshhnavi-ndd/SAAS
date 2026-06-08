"""Tests for authentication endpoints."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
import asyncio

from app.main import app
from app.database.connection import Base, get_db
from app.utils.security import decode_token


@pytest.fixture
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def test_db():
    """Create an in-memory test database."""
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

    async def override_get_db():
        async with AsyncSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db

    yield AsyncSessionLocal

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest.fixture
async def client(test_db):
    """Create an async test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_signup_creates_tenant_and_user(client):
    """Test that signup creates a tenant and user."""
    response = await client.post(
        "/api/v1/auth/signup",
        json={
            "tenant_name": "Test Company",
            "email": "user@test.com",
            "password": "secure123",
        },
    )

    assert response.status_code == 200
    data = response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert "user_id" in data
    assert "tenant_id" in data

    # Verify token contains claims
    payload = decode_token(data["access_token"])
    assert payload["sub"] == data["user_id"]
    assert payload["tenant_id"] == data["tenant_id"]


@pytest.mark.asyncio
async def test_login_with_valid_credentials(client):
    """Test login with valid credentials."""
    # First signup
    signup_response = await client.post(
        "/api/v1/auth/signup",
        json={
            "tenant_name": "Test Company",
            "email": "user@test.com",
            "password": "secure123",
        },
    )
    assert signup_response.status_code == 200

    # Then login
    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "user@test.com",
            "password": "secure123",
        },
    )

    assert login_response.status_code == 200
    data = login_response.json()

    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_with_invalid_password(client):
    """Test login with invalid password."""
    # Signup
    await client.post(
        "/api/v1/auth/signup",
        json={
            "tenant_name": "Test Company",
            "email": "user@test.com",
            "password": "secure123",
        },
    )

    # Try to login with wrong password
    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "user@test.com",
            "password": "wrongpassword",
        },
    )

    assert login_response.status_code == 401
    assert "detail" in login_response.json()


@pytest.mark.asyncio
async def test_login_with_nonexistent_email(client):
    """Test login with non-existent email."""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "nonexistent@test.com",
            "password": "anypassword",
        },
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_health_endpoint_no_auth(client):
    """Test that health endpoint works without authentication."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_signup_with_invalid_email(client):
    """Test signup with invalid email."""
    response = await client.post(
        "/api/v1/auth/signup",
        json={
            "tenant_name": "Test Company",
            "email": "invalid-email",
            "password": "secure123",
        },
    )

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_signup_with_missing_fields(client):
    """Test signup with missing required fields."""
    response = await client.post(
        "/api/v1/auth/signup",
        json={
            "tenant_name": "Test Company",
            "email": "user@test.com",
            # Missing password
        },
    )

    assert response.status_code == 422  # Validation error


@pytest.mark.asyncio
async def test_jwt_token_structure(client):
    """Test JWT token structure and claims."""
    response = await client.post(
        "/api/v1/auth/signup",
        json={
            "tenant_name": "Test Company",
            "email": "user@test.com",
            "password": "secure123",
        },
    )

    data = response.json()
    token = data["access_token"]

    # Decode token
    payload = decode_token(token)

    # Verify required claims
    assert "sub" in payload  # user_id
    assert "tenant_id" in payload
    assert "exp" in payload  # expiration

    # Verify values match response
    assert payload["sub"] == data["user_id"]
    assert payload["tenant_id"] == data["tenant_id"]


@pytest.mark.asyncio
async def test_protected_endpoint_without_token(client):
    """Test that protected endpoints reject requests without token."""
    response = await client.get("/api/v1/tenants")
    assert response.status_code == 403  # Forbidden (missing auth)


@pytest.mark.asyncio
async def test_protected_endpoint_with_invalid_token(client):
    """Test that protected endpoints reject invalid tokens."""
    response = await client.get(
        "/api/v1/tenants",
        headers={"Authorization": "Bearer invalid_token_123"},
    )
    assert response.status_code == 403 or response.status_code == 401

