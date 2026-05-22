import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register(client: AsyncClient):
    """Test user registration"""
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "newuser@example.com", "password": "password123"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["data"]["email"] == "newuser@example.com"


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    """Test registration with duplicate email"""
    await client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "password123"},
    )
    response = await client.post(
        "/api/v1/auth/register",
        json={"email": "test@example.com", "password": "password456"},
    )
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_login(client: AsyncClient, user):
    """Test user login"""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": "testpassword"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data["data"]
    assert "refresh_token" in data["data"]


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient, user):
    """Test login with invalid password"""
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": "wrongpassword"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient, user):
    """Test token refresh"""
    login_response = await client.post(
        "/api/v1/auth/login",
        json={"email": user.email, "password": "testpassword"},
    )
    refresh_token = login_response.json()["data"]["refresh_token"]

    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data["data"]
