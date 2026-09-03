import uuid
import pytest
from httpx import AsyncClient
from datetime import date
from app.models.product import Product


@pytest.mark.asyncio
async def test_create_sale(client: AsyncClient, auth_headers, product):
    """Test creating a sale"""
    response = await client.post(
        "/api/v1/sales",
        headers=auth_headers,
        json={
            "channel_id": None,
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
    assert data["data"]["total_amount"] == "100.00"


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
async def test_list_sales_pagination(client: AsyncClient, auth_headers, product):
    """GET /sales paginates like GET /products, newest sale_date first"""
    for day in ("2024-01-01", "2024-01-02", "2024-01-03"):
        await client.post(
            "/api/v1/sales",
            headers=auth_headers,
            json={
                "sale_date": day,
                "items": [{"product_id": str(product.id), "quantity": 1, "price": "10.00"}],
            },
        )

    response = await client.get("/api/v1/sales?page=1&per_page=2", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert len(body["data"]) == 2
    assert body["data"][0]["sale_date"] == "2024-01-03"
    assert body["meta"] == {"total": 3, "page": 1, "per_page": 2, "pages": 2}

    response2 = await client.get("/api/v1/sales?page=2&per_page=2", headers=auth_headers)
    body2 = response2.json()
    assert len(body2["data"]) == 1
    assert body2["data"][0]["sale_date"] == "2024-01-01"


@pytest.mark.asyncio
async def test_list_sales_includes_items_with_product_name(client: AsyncClient, auth_headers, product):
    """GET /sales must include items (with product_name) so the UI can show a row per product"""
    await client.post(
        "/api/v1/sales",
        headers=auth_headers,
        json={
            "sale_date": "2024-01-15",
            "items": [
                {"product_id": str(product.id), "quantity": 2, "price": "50.00"},
                {"product_id": None, "quantity": 1, "price": "5.00"},
            ],
        },
    )

    response = await client.get("/api/v1/sales", headers=auth_headers)
    assert response.status_code == 200
    sale = response.json()["data"][0]
    assert len(sale["items"]) == 2
    names = {item["product_name"] for item in sale["items"]}
    assert product.name in names
    assert None in names


@pytest.mark.asyncio
async def test_list_sales_filters_by_product_id(client: AsyncClient, auth_headers, product, db_session):
    """?product_id= should only return sales that include that product,
    even when another sale's items belong to a different product."""
    other = Product(id=uuid.uuid4(), user_id=product.user_id, name="Other Toy", sale_price="20.00", stock_qty=5)
    db_session.add(other)
    await db_session.commit()

    await client.post(
        "/api/v1/sales",
        headers=auth_headers,
        json={
            "sale_date": "2024-01-15",
            "items": [{"product_id": str(product.id), "quantity": 1, "price": "50.00"}],
        },
    )
    await client.post(
        "/api/v1/sales",
        headers=auth_headers,
        json={
            "sale_date": "2024-01-16",
            "items": [{"product_id": str(other.id), "quantity": 1, "price": "20.00"}],
        },
    )

    response = await client.get(f"/api/v1/sales?product_id={product.id}", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["meta"]["total"] == 1
    assert len(body["data"]) == 1
    assert body["data"][0]["items"][0]["product_id"] == str(product.id)


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


@pytest.mark.asyncio
async def test_create_sale_rejects_non_positive_quantity(client: AsyncClient, auth_headers, product):
    """Quantity <= 0 must be rejected — it would inflate stock instead of deducting it"""
    response = await client.post(
        "/api/v1/sales",
        headers=auth_headers,
        json={
            "sale_date": "2024-01-15",
            "items": [
                {
                    "product_id": str(product.id),
                    "quantity": 0,
                    "price": "50.00",
                }
            ],
        },
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_sale_rejects_negative_price(client: AsyncClient, auth_headers, product):
    """Negative price must be rejected — it would make total_amount negative"""
    response = await client.post(
        "/api/v1/sales",
        headers=auth_headers,
        json={
            "sale_date": "2024-01-15",
            "items": [
                {
                    "product_id": str(product.id),
                    "quantity": 1,
                    "price": "-10.00",
                }
            ],
        },
    )
    assert response.status_code == 422
