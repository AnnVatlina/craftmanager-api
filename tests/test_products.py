import pytest
from httpx import AsyncClient
from decimal import Decimal
from sqlalchemy.future import select
from app.models.product_production import ProductProduction


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
async def test_create_product_records_initial_production(client: AsyncClient, auth_headers, db_session):
    response = await client.post(
        "/api/v1/products",
        headers=auth_headers,
        json={
            "name": "Initial Stock Toy",
            "sale_price": "25.00",
            "stock_qty": 4,
            "produced_at": "2026-08-01",
        },
    )
    assert response.status_code == 201
    product_id = response.json()["data"]["id"]

    result = await db_session.execute(
        select(ProductProduction).where(ProductProduction.product_id == product_id)
    )
    production = result.scalar_one()
    assert production.quantity == 4
    assert production.produced_at.isoformat() == "2026-08-01"
    assert production.source == "production"


@pytest.mark.asyncio
async def test_restock_product_records_production(client: AsyncClient, auth_headers, product, db_session):
    response = await client.post(
        f"/api/v1/products/{product.id}/restock",
        headers=auth_headers,
        json={"qty": 3, "produced_at": "2026-08-15"},
    )
    assert response.status_code == 200
    assert response.json()["data"]["stock_qty"] == 13

    result = await db_session.execute(
        select(ProductProduction).where(ProductProduction.product_id == product.id)
    )
    production = result.scalar_one()
    assert production.quantity == 3
    assert production.produced_at.isoformat() == "2026-08-15"


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


@pytest.mark.asyncio
async def test_search_products_by_name_substring(client: AsyncClient, auth_headers, product):
    """Test that ?search matches a case-insensitive substring of the name"""
    await client.post(
        "/api/v1/products",
        headers=auth_headers,
        json={"name": "Plush Bunny", "sale_price": "45.00"},
    )

    response = await client.get(
        "/api/v1/products",
        headers=auth_headers,
        params={"search": "bunny"},
    )
    assert response.status_code == 200
    data = response.json()["data"]
    names = [p["name"] for p in data]
    assert "Plush Bunny" in names
    assert product.name not in names  # "Test Toy" fixture doesn't contain "bunny"


@pytest.mark.asyncio
async def test_search_products_no_match(client: AsyncClient, auth_headers, product):
    """Test that ?search with no matches returns an empty list, not an error"""
    response = await client.get(
        "/api/v1/products",
        headers=auth_headers,
        params={"search": "nonexistent-xyz"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["data"] == []
    assert data["meta"]["total"] == 0


@pytest.mark.asyncio
async def test_search_products_isolated_by_user(client: AsyncClient, second_auth_headers, product):
    """Test that ?search never returns another user's products"""
    response = await client.get(
        "/api/v1/products",
        headers=second_auth_headers,
        params={"search": "Test"},  # substring of the other user's "Test Toy"
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert product.name not in [p["name"] for p in data]
