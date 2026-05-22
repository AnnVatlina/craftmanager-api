import pytest
from httpx import AsyncClient
from decimal import Decimal


@pytest.mark.asyncio
async def test_create_product(client: AsyncClient, auth_headers):
    """Test creating a product"""
    response = await client.post(
        "/api/v1/products",
        headers=auth_headers,
        json={
            "name": "Soft Toy",
            "description": "A soft plush toy",
            "category": "soft",
            "sale_price": "50.00",
            "stock_qty": 10,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["data"]["name"] == "Soft Toy"
    assert data["data"]["sale_price"] == "50.00"


@pytest.mark.asyncio
async def test_list_products(client: AsyncClient, auth_headers, product):
    """Test listing products"""
    response = await client.get(
        "/api/v1/products",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) >= 1


@pytest.mark.asyncio
async def test_get_product(client: AsyncClient, auth_headers, product):
    """Test getting a specific product"""
    response = await client.get(
        f"/api/v1/products/{product.id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["name"] == product.name
    assert "materials" in data["data"]


@pytest.mark.asyncio
async def test_update_product(client: AsyncClient, auth_headers, product):
    """Test updating a product"""
    response = await client.put(
        f"/api/v1/products/{product.id}",
        headers=auth_headers,
        json={
            "name": "Updated Toy",
            "sale_price": "60.00",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["name"] == "Updated Toy"
    assert data["data"]["sale_price"] == "60.00"


@pytest.mark.asyncio
async def test_delete_product(client: AsyncClient, auth_headers, product):
    """Test deleting a product"""
    response = await client.delete(
        f"/api/v1/products/{product.id}",
        headers=auth_headers,
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_add_material_to_product(client: AsyncClient, auth_headers, product, material):
    """Test adding a material to product composition"""
    response = await client.post(
        f"/api/v1/products/{product.id}/materials",
        headers=auth_headers,
        json={
            "material_id": str(material.id),
            "quantity": "100.00",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["data"]["material_id"] == str(material.id)
    assert data["data"]["quantity"] == "100.0000"


@pytest.mark.asyncio
async def test_get_product_materials(client: AsyncClient, auth_headers, product, material):
    """Test getting product materials"""
    # First add material
    await client.post(
        f"/api/v1/products/{product.id}/materials",
        headers=auth_headers,
        json={
            "material_id": str(material.id),
            "quantity": "100.00",
        },
    )

    response = await client.get(
        f"/api/v1/products/{product.id}/materials",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) >= 1


@pytest.mark.asyncio
async def test_remove_material_from_product(client: AsyncClient, auth_headers, product, material):
    """Test removing a material from product"""
    # First add material
    await client.post(
        f"/api/v1/products/{product.id}/materials",
        headers=auth_headers,
        json={
            "material_id": str(material.id),
            "quantity": "100.00",
        },
    )

    response = await client.delete(
        f"/api/v1/products/{product.id}/materials/{material.id}",
        headers=auth_headers,
    )
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_product_cost_price_calculation(client: AsyncClient, auth_headers, product, material):
    """Test that cost_price is calculated correctly"""
    # Add material to product
    await client.post(
        f"/api/v1/products/{product.id}/materials",
        headers=auth_headers,
        json={
            "material_id": str(material.id),
            "quantity": "10.0",
        },
    )

    response = await client.get(
        f"/api/v1/products/{product.id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    # cost_price = 10.0 * 10.00 = 100.00
    assert data["data"]["cost_price"] == "100.00"


@pytest.mark.asyncio
async def test_product_not_found_for_other_user(client: AsyncClient, second_auth_headers, product):
    """Test that users can't access other users' products"""
    response = await client.get(
        f"/api/v1/products/{product.id}",
        headers=second_auth_headers,
    )
    assert response.status_code == 404
