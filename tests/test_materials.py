import pytest
from httpx import AsyncClient
from decimal import Decimal


@pytest.mark.asyncio
async def test_create_material(client: AsyncClient, auth_headers):
    """Test creating a material"""
    response = await client.post(
        "/api/v1/materials",
        headers=auth_headers,
        json={
            "name": "Cotton",
            "unit": "g",
            "price_per_unit": "10.50",
            "stock_qty": "1000.00",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["data"]["name"] == "Cotton"
    assert data["data"]["unit"] == "g"


@pytest.mark.asyncio
async def test_list_materials(client: AsyncClient, auth_headers, material):
    """Test listing materials"""
    response = await client.get(
        "/api/v1/materials",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) >= 1
    assert data["meta"]["total"] >= 1


@pytest.mark.asyncio
async def test_get_material(client: AsyncClient, auth_headers, material):
    """Test getting a specific material"""
    response = await client.get(
        f"/api/v1/materials/{material.id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["name"] == material.name


@pytest.mark.asyncio
async def test_get_material_not_found(client: AsyncClient, auth_headers):
    """Test getting non-existent material"""
    import uuid
    response = await client.get(
        f"/api/v1/materials/{uuid.uuid4()}",
        headers=auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_material(client: AsyncClient, auth_headers, material):
    """Test updating a material"""
    response = await client.put(
        f"/api/v1/materials/{material.id}",
        headers=auth_headers,
        json={
            "name": "Updated Cotton",
            "price_per_unit": "15.00",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["name"] == "Updated Cotton"
    assert data["data"]["price_per_unit"] == "15.0000"


@pytest.mark.asyncio
async def test_delete_material(client: AsyncClient, auth_headers, material):
    """Test deleting a material"""
    response = await client.delete(
        f"/api/v1/materials/{material.id}",
        headers=auth_headers,
    )
    assert response.status_code == 204

    # Verify it's deleted
    get_response = await client.get(
        f"/api/v1/materials/{material.id}",
        headers=auth_headers,
    )
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_restock_material(client: AsyncClient, auth_headers, material):
    """Test restocking a material"""
    response = await client.post(
        f"/api/v1/materials/{material.id}/restock",
        headers=auth_headers,
        json={
            "qty": "500.00",
            "price_per_unit": "12.00",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["stock_qty"] == str(Decimal("1000.000") + Decimal("500.00"))


@pytest.mark.asyncio
async def test_material_not_found_for_other_user(client: AsyncClient, second_auth_headers, material):
    """Test that users can't access other users' materials"""
    response = await client.get(
        f"/api/v1/materials/{material.id}",
        headers=second_auth_headers,
    )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_no_auth_returns_403(client: AsyncClient):
    """Test that requests without auth return 403"""
    response = await client.get("/api/v1/materials")
    assert response.status_code == 403
