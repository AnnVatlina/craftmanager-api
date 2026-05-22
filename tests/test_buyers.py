import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_buyers_crud(client: AsyncClient, auth_headers):
    """Test buyer CRUD operations"""
    # Create
    create_response = await client.post(
        "/api/v1/buyers",
        headers=auth_headers,
        json={
            "name": "John Doe",
            "contact": "+1234567890",
            "notes": "VIP customer",
        },
    )
    assert create_response.status_code == 201
    buyer_id = create_response.json()["data"]["id"]

    # Read
    get_response = await client.get(
        f"/api/v1/buyers/{buyer_id}",
        headers=auth_headers,
    )
    assert get_response.status_code == 200

    # Update
    update_response = await client.put(
        f"/api/v1/buyers/{buyer_id}",
        headers=auth_headers,
        json={"name": "Jane Doe"},
    )
    assert update_response.status_code == 200

    # Delete
    delete_response = await client.delete(
        f"/api/v1/buyers/{buyer_id}",
        headers=auth_headers,
    )
    assert delete_response.status_code == 204


@pytest.mark.asyncio
async def test_buyer_not_found_for_other_user(client: AsyncClient, second_auth_headers, buyer):
    """Test that users can't access other users' buyers"""
    response = await client.get(
        f"/api/v1/buyers/{buyer.id}",
        headers=second_auth_headers,
    )
    assert response.status_code == 404
