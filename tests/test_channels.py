import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_channels_crud(client: AsyncClient, auth_headers):
    """Test sales channel CRUD"""
    # Create fair
    create = await client.post(
        "/api/v1/channels",
        headers=auth_headers,
        json={"name": "Весенняя ярмарка", "type": "ярмарка", "event_date": "2026-05-01", "location": "Минск"},
    )
    assert create.status_code == 201
    channel_id = create.json()["data"]["id"]
    assert create.json()["data"]["type"] == "ярмарка"

    # List
    lst = await client.get("/api/v1/channels", headers=auth_headers)
    assert lst.status_code == 200
    assert len(lst.json()["data"]) >= 1

    # Get detail
    get = await client.get(f"/api/v1/channels/{channel_id}", headers=auth_headers)
    assert get.status_code == 200
    assert get.json()["data"]["name"] == "Весенняя ярмарка"

    # Update
    upd = await client.put(
        f"/api/v1/channels/{channel_id}",
        headers=auth_headers,
        json={"name": "Летняя ярмарка"},
    )
    assert upd.status_code == 200
    assert upd.json()["data"]["name"] == "Летняя ярмарка"

    # Delete
    delete = await client.delete(f"/api/v1/channels/{channel_id}", headers=auth_headers)
    assert delete.status_code == 204


@pytest.mark.asyncio
async def test_channel_dm(client: AsyncClient, auth_headers):
    """Test creating a DM channel"""
    res = await client.post(
        "/api/v1/channels",
        headers=auth_headers,
        json={"name": "Instagram", "type": "лс"},
    )
    assert res.status_code == 201
    assert res.json()["data"]["event_date"] is None


@pytest.mark.asyncio
async def test_channel_not_found_for_other_user(client: AsyncClient, auth_headers, second_auth_headers):
    """Test user isolation"""
    create = await client.post(
        "/api/v1/channels",
        headers=auth_headers,
        json={"name": "Ярмарка", "type": "ярмарка"},
    )
    channel_id = create.json()["data"]["id"]

    res = await client.get(f"/api/v1/channels/{channel_id}", headers=second_auth_headers)
    assert res.status_code == 404
