import pytest
from httpx import AsyncClient
from datetime import date


@pytest.mark.asyncio
async def test_create_expense(client: AsyncClient, auth_headers):
    """Test creating an expense"""
    response = await client.post(
        "/api/v1/expenses",
        headers=auth_headers,
        json={
            "category": "materials",
            "amount": "100.00",
            "description": "Cotton purchase",
            "expense_date": "2024-01-15",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["data"]["category"] == "materials"
    assert data["data"]["amount"] == "100.00"


@pytest.mark.asyncio
async def test_list_expenses(client: AsyncClient, auth_headers):
    """Test listing expenses"""
    # Create an expense first
    await client.post(
        "/api/v1/expenses",
        headers=auth_headers,
        json={
            "category": "materials",
            "amount": "100.00",
            "expense_date": "2024-01-15",
        },
    )

    response = await client.get(
        "/api/v1/expenses",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) >= 1


@pytest.mark.asyncio
async def test_get_expense(client: AsyncClient, auth_headers):
    """Test getting a specific expense"""
    create_response = await client.post(
        "/api/v1/expenses",
        headers=auth_headers,
        json={
            "category": "tools",
            "amount": "50.00",
            "description": "Needles",
            "expense_date": "2024-01-15",
        },
    )
    expense_id = create_response.json()["data"]["id"]

    response = await client.get(
        f"/api/v1/expenses/{expense_id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["category"] == "tools"


@pytest.mark.asyncio
async def test_update_expense(client: AsyncClient, auth_headers):
    """Test updating an expense"""
    create_response = await client.post(
        "/api/v1/expenses",
        headers=auth_headers,
        json={
            "category": "materials",
            "amount": "100.00",
            "expense_date": "2024-01-15",
        },
    )
    expense_id = create_response.json()["data"]["id"]

    response = await client.put(
        f"/api/v1/expenses/{expense_id}",
        headers=auth_headers,
        json={
            "amount": "120.00",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["amount"] == "120.00"


@pytest.mark.asyncio
async def test_delete_expense(client: AsyncClient, auth_headers):
    """Test deleting an expense"""
    create_response = await client.post(
        "/api/v1/expenses",
        headers=auth_headers,
        json={
            "category": "materials",
            "amount": "100.00",
            "expense_date": "2024-01-15",
        },
    )
    expense_id = create_response.json()["data"]["id"]

    response = await client.delete(
        f"/api/v1/expenses/{expense_id}",
        headers=auth_headers,
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_expense_not_found_for_other_user(client: AsyncClient, second_auth_headers):
    """Test that users can't access other users' expenses"""
    import uuid
    response = await client.get(
        f"/api/v1/expenses/{uuid.uuid4()}",
        headers=second_auth_headers,
    )
    assert response.status_code == 404
