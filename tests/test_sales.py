import pytest
from httpx import AsyncClient
from datetime import date


@pytest.mark.asyncio
async def test_create_sale(client: AsyncClient, auth_headers, product):
    """Test creating a sale"""
    response = await client.post(
        "/api/v1/sales",
        headers=auth_headers,
        json={
            "buyer_id": None,
            "sale_date": "2024-01-15",
            "notes": "Test sale",
            "items": [
                {
                    "product_id": str(product.id),
                    "quantity": 2,
                    "price": "50.00",
                }
            ],
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["data"]["total_amount"] == "100.0"


@pytest.mark.asyncio
async def test_list_sales(client: AsyncClient, auth_headers, product):
    """Test listing sales"""
    await client.post(
        "/api/v1/sales",
        headers=auth_headers,
        json={
            "sale_date": "2024-01-15",
            "items": [
                {
                    "product_id": str(product.id),
                    "quantity": 1,
                    "price": "50.00",
                }
            ],
        },
    )

    response = await client.get(
        "/api/v1/sales",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) >= 1


@pytest.mark.asyncio
async def test_get_sale(client: AsyncClient, auth_headers, product):
    """Test getting a specific sale"""
    create_response = await client.post(
        "/api/v1/sales",
        headers=auth_headers,
        json={
            "sale_date": "2024-01-15",
            "items": [
                {
                    "product_id": str(product.id),
                    "quantity": 1,
                    "price": "50.00",
                }
            ],
        },
    )
    sale_id = create_response.json()["data"]["id"]

    response = await client.get(
        f"/api/v1/sales/{sale_id}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]["items"]) == 1


@pytest.mark.asyncio
async def test_sale_stock_deduction(client: AsyncClient, auth_headers, product):
    """Test that sale deducts product stock"""
    initial_stock = product.stock_qty

    await client.post(
        "/api/v1/sales",
        headers=auth_headers,
        json={
            "sale_date": "2024-01-15",
            "items": [
                {
                    "product_id": str(product.id),
                    "quantity": 3,
                    "price": "50.00",
                }
            ],
        },
    )

    # Get product to check stock
    response = await client.get(
        f"/api/v1/products/{product.id}",
        headers=auth_headers,
    )
    data = response.json()
    assert data["data"]["stock_qty"] == initial_stock - 3


@pytest.mark.asyncio
async def test_delete_sale_restores_stock(client: AsyncClient, auth_headers, product):
    """Test that deleting a sale restores product stock"""
    initial_stock = product.stock_qty

    create_response = await client.post(
        "/api/v1/sales",
        headers=auth_headers,
        json={
            "sale_date": "2024-01-15",
            "items": [
                {
                    "product_id": str(product.id),
                    "quantity": 3,
                    "price": "50.00",
                }
            ],
        },
    )
    sale_id = create_response.json()["data"]["id"]

    # Delete sale
    await client.delete(
        f"/api/v1/sales/{sale_id}",
        headers=auth_headers,
    )

    # Check stock restored
    response = await client.get(
        f"/api/v1/products/{product.id}",
        headers=auth_headers,
    )
    data = response.json()
    assert data["data"]["stock_qty"] == initial_stock


@pytest.mark.asyncio
async def test_sale_not_found_for_other_user(client: AsyncClient, second_auth_headers, product):
    """Test that users can't access other users' sales"""
    import uuid
    response = await client.get(
        f"/api/v1/sales/{uuid.uuid4()}",
        headers=second_auth_headers,
    )
    assert response.status_code == 404
