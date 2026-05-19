"""Tests for the authentication and RBAC module."""

import pytest
from httpx import AsyncClient, ASGITransport

from main import app


@pytest.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


# ── Registration ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_register_success(async_client):
    """Registration with valid data returns 201 and user info."""
    response = await async_client.post("/api/auth/register", json={
        "username": "newuser",
        "password": "securepass",
        "role": "viewer",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "newuser"
    assert data["role"] == "viewer"
    assert "message" in data


@pytest.mark.asyncio
async def test_register_duplicate_username(async_client):
    """Registering the same username twice returns 409."""
    payload = {"username": "dupeuser", "password": "securepass", "role": "viewer"}
    await async_client.post("/api/auth/register", json=payload)
    response = await async_client.post("/api/auth/register", json=payload)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_register_short_username(async_client):
    """Username under 3 chars is rejected."""
    response = await async_client.post("/api/auth/register", json={
        "username": "ab", "password": "securepass", "role": "viewer",
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_short_password(async_client):
    """Password under 6 chars is rejected."""
    response = await async_client.post("/api/auth/register", json={
        "username": "validname", "password": "short", "role": "viewer",
    })
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_register_commander_role(async_client):
    """Commander role registration works."""
    response = await async_client.post("/api/auth/register", json={
        "username": "cmduser", "password": "securepass", "role": "commander",
    })
    assert response.status_code == 201
    assert response.json()["role"] == "commander"


# ── Login ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_login_success(async_client):
    """Valid credentials return a JWT token."""
    # First register
    await async_client.post("/api/auth/register", json={
        "username": "loginuser", "password": "testpass123", "role": "viewer",
    })
    # Then login
    response = await async_client.post("/api/auth/login", data={
        "username": "loginuser", "password": "testpass123",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["role"] == "viewer"
    assert data["username"] == "loginuser"


@pytest.mark.asyncio
async def test_login_wrong_password(async_client):
    """Wrong password returns 401."""
    await async_client.post("/api/auth/register", json={
        "username": "wrongpw", "password": "correctpass", "role": "viewer",
    })
    response = await async_client.post("/api/auth/login", data={
        "username": "wrongpw", "password": "wrongpass",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_user(async_client):
    """Non-existent user returns 401."""
    response = await async_client.post("/api/auth/login", data={
        "username": "nouser", "password": "anypass",
    })
    assert response.status_code == 401


# ── /api/auth/me ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_me_with_valid_token(async_client):
    """Authenticated /me endpoint returns user info."""
    await async_client.post("/api/auth/register", json={
        "username": "meuser", "password": "testpass123", "role": "commander",
    })
    login = await async_client.post("/api/auth/login", data={
        "username": "meuser", "password": "testpass123",
    })
    token = login.json()["access_token"]

    response = await async_client.get("/api/auth/me", headers={
        "Authorization": f"Bearer {token}",
    })
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "meuser"
    assert data["role"] == "commander"


@pytest.mark.asyncio
async def test_me_without_token(async_client):
    """/me without token returns 401."""
    response = await async_client.get("/api/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_me_with_invalid_token(async_client):
    """/me with garbage token returns 401."""
    response = await async_client.get("/api/auth/me", headers={
        "Authorization": "Bearer invalidtoken123",
    })
    assert response.status_code == 401
