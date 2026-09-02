import pytest
from httpx import AsyncClient


async def _create_channel(client, headers, *, name, ch_type="ярмарка", event_date=None):
    body = {"name": name, "type": ch_type}
    if event_date:
        body["event_date"] = event_date
    res = await client.post("/api/v1/channels", headers=headers, json=body)
    assert res.status_code == 201
    return res.json()["data"]["id"]


async def _create_product(client, headers, *, name, sale_price="20.00"):
    res = await client.post(
        "/api/v1/products", headers=headers,
        json={"name": name, "sale_price": sale_price, "stock_qty": 10},
    )
    assert res.status_code == 201
    return res.json()["data"]["id"]


@pytest.mark.asyncio
async def test_fair_channels_summary_combines_planned_and_sold(client: AsyncClient, auth_headers):
    channel_id = await _create_channel(
        client, auth_headers, name="Весенняя ярмарка", event_date="2024-05-01",
    )
    product_id = await _create_product(client, auth_headers, name="Мишка", sale_price="20.00")

    await client.post(
        f"/api/v1/fair-prep/{channel_id}/items", headers=auth_headers,
        json={"product_id": product_id, "planned_qty": 5},
    )
    await client.post(
        "/api/v1/sales", headers=auth_headers,
        json={
            "channel_id": channel_id,
            "sale_date": "2024-05-02",
            "items": [{"product_id": product_id, "quantity": 2, "price": "20.00"}],
        },
    )

    res = await client.get("/api/v1/dashboard/fair-channels", headers=auth_headers)
    assert res.status_code == 200
    rows = res.json()["data"]
    assert len(rows) == 1
    row = rows[0]
    assert row["channel_name"] == "Весенняя ярмарка"
    assert row["event_date"] == "2024-05-01"
    assert row["total_planned"] == 5
    assert row["total_sold"] == 2
    assert row["total_revenue"] == "40.00"


@pytest.mark.asyncio
async def test_fair_channels_summary_excludes_non_fair_channels(client: AsyncClient, auth_headers):
    await _create_channel(client, auth_headers, name="Instagram", ch_type="лс")

    res = await client.get("/api/v1/dashboard/fair-channels", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["data"] == []


@pytest.mark.asyncio
async def test_fair_channels_summary_zero_when_nothing_planned_or_sold(client: AsyncClient, auth_headers):
    await _create_channel(client, auth_headers, name="Летняя ярмарка")

    res = await client.get("/api/v1/dashboard/fair-channels", headers=auth_headers)
    assert res.status_code == 200
    row = res.json()["data"][0]
    assert row["total_planned"] == 0
    assert row["total_sold"] == 0
    assert row["total_revenue"] == "0"


@pytest.mark.asyncio
async def test_fair_channels_summary_isolated_by_user(client: AsyncClient, auth_headers, second_auth_headers):
    await _create_channel(client, auth_headers, name="Моя ярмарка")

    res = await client.get("/api/v1/dashboard/fair-channels", headers=second_auth_headers)
    assert res.status_code == 200
    assert res.json()["data"] == []
