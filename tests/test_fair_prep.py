import pytest
from httpx import AsyncClient


# ── helpers ──────────────────────────────────────────────────────────────────

async def _create_channel(client, headers, *, name, ch_type="ярмарка", event_date=None):
    body = {"name": name, "type": ch_type}
    if event_date:
        body["event_date"] = event_date
    res = await client.post("/api/v1/channels", headers=headers, json=body)
    assert res.status_code == 201
    return res.json()["data"]["id"]


async def _create_product(client, headers, *, name, stock_qty=5, sale_price="20.00", category=None):
    body = {"name": name, "sale_price": sale_price, "stock_qty": stock_qty}
    if category:
        body["category"] = category
    res = await client.post("/api/v1/products", headers=headers, json=body)
    assert res.status_code == 201
    return res.json()["data"]["id"]


# ── list channels ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_fair_channels_returns_only_fairs(client: AsyncClient, auth_headers):
    """Only ярмарка-type channels appear in the fair-prep channel list."""
    await _create_channel(client, auth_headers, name="Весенняя ярмарка", ch_type="ярмарка")
    await _create_channel(client, auth_headers, name="Instagram", ch_type="лс")
    await _create_channel(client, auth_headers, name="Прочее", ch_type="другое")

    res = await client.get("/api/v1/fair-prep/channels", headers=auth_headers)
    assert res.status_code == 200
    names = [c["name"] for c in res.json()["data"]]
    assert "Весенняя ярмарка" in names
    assert "Instagram" not in names
    assert "Прочее" not in names


@pytest.mark.asyncio
async def test_list_fair_channels_empty(client: AsyncClient, auth_headers):
    res = await client.get("/api/v1/fair-prep/channels", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["data"] == []


# ── get prep list ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_prep_empty_list(client: AsyncClient, auth_headers):
    """New channel has empty prep list with zeroed summary."""
    channel_id = await _create_channel(client, auth_headers, name="Ярмарка", event_date="2026-06-01")

    res = await client.get(f"/api/v1/fair-prep/{channel_id}", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["items"] == []
    assert data["summary"]["total_positions"] == 0
    assert data["summary"]["total_planned"] == 0
    assert data["summary"]["total_need_to_make"] == 0
    assert data["channel"]["name"] == "Ярмарка"


@pytest.mark.asyncio
async def test_get_prep_channel_not_found(client: AsyncClient, auth_headers):
    res = await client.get("/api/v1/fair-prep/00000000-0000-0000-0000-000000000000", headers=auth_headers)
    assert res.status_code == 404


# ── add item ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_add_item_returns_updated_list(client: AsyncClient, auth_headers):
    channel_id = await _create_channel(client, auth_headers, name="Ярмарка")
    product_id = await _create_product(client, auth_headers, name="Игрушка", stock_qty=3)

    res = await client.post(
        f"/api/v1/fair-prep/{channel_id}/items",
        headers=auth_headers,
        json={"product_id": product_id, "planned_qty": 5},
    )
    assert res.status_code == 201
    data = res.json()["data"]
    assert len(data["items"]) == 1
    item = data["items"][0]
    assert item["product_name"] == "Игрушка"
    assert item["planned_qty"] == 5
    assert item["stock_qty"] == 3
    assert item["need_to_make"] == 2          # 5 - 3 = 2, server-side


@pytest.mark.asyncio
async def test_add_item_need_to_make_zero_when_stock_sufficient(client: AsyncClient, auth_headers):
    """need_to_make must be 0 when stock >= planned."""
    channel_id = await _create_channel(client, auth_headers, name="Ярмарка")
    product_id = await _create_product(client, auth_headers, name="Зайка", stock_qty=10)

    res = await client.post(
        f"/api/v1/fair-prep/{channel_id}/items",
        headers=auth_headers,
        json={"product_id": product_id, "planned_qty": 7},
    )
    assert res.status_code == 201
    item = res.json()["data"]["items"][0]
    assert item["need_to_make"] == 0


@pytest.mark.asyncio
async def test_add_duplicate_product_returns_400(client: AsyncClient, auth_headers):
    channel_id = await _create_channel(client, auth_headers, name="Ярмарка")
    product_id = await _create_product(client, auth_headers, name="Мишка")

    await client.post(
        f"/api/v1/fair-prep/{channel_id}/items",
        headers=auth_headers,
        json={"product_id": product_id, "planned_qty": 3},
    )
    res = await client.post(
        f"/api/v1/fair-prep/{channel_id}/items",
        headers=auth_headers,
        json={"product_id": product_id, "planned_qty": 5},
    )
    assert res.status_code == 400


# ── update item ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_update_item_recalculates_need_to_make(client: AsyncClient, auth_headers):
    channel_id = await _create_channel(client, auth_headers, name="Ярмарка")
    product_id = await _create_product(client, auth_headers, name="Лиса", stock_qty=4)

    add_res = await client.post(
        f"/api/v1/fair-prep/{channel_id}/items",
        headers=auth_headers,
        json={"product_id": product_id, "planned_qty": 3},
    )
    item_id = add_res.json()["data"]["items"][0]["id"]

    res = await client.put(
        f"/api/v1/fair-prep/{channel_id}/items/{item_id}",
        headers=auth_headers,
        json={"planned_qty": 10},
    )
    assert res.status_code == 200
    item = res.json()["data"]["items"][0]
    assert item["planned_qty"] == 10
    assert item["need_to_make"] == 6          # 10 - 4 = 6


@pytest.mark.asyncio
async def test_update_item_not_found(client: AsyncClient, auth_headers):
    channel_id = await _create_channel(client, auth_headers, name="Ярмарка")
    res = await client.put(
        f"/api/v1/fair-prep/{channel_id}/items/00000000-0000-0000-0000-000000000000",
        headers=auth_headers,
        json={"planned_qty": 5},
    )
    assert res.status_code == 404


# ── remove item ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_remove_item_returns_updated_list(client: AsyncClient, auth_headers):
    channel_id = await _create_channel(client, auth_headers, name="Ярмарка")
    p1 = await _create_product(client, auth_headers, name="Кот")
    p2 = await _create_product(client, auth_headers, name="Собака")

    await client.post(f"/api/v1/fair-prep/{channel_id}/items", headers=auth_headers,
                      json={"product_id": p1, "planned_qty": 2})
    add_res = await client.post(f"/api/v1/fair-prep/{channel_id}/items", headers=auth_headers,
                                json={"product_id": p2, "planned_qty": 3})
    item_id = next(i["id"] for i in add_res.json()["data"]["items"] if i["product_name"] == "Собака")

    res = await client.delete(f"/api/v1/fair-prep/{channel_id}/items/{item_id}", headers=auth_headers)
    assert res.status_code == 200
    remaining = [i["product_name"] for i in res.json()["data"]["items"]]
    assert "Собака" not in remaining
    assert "Кот" in remaining


# ── summary ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_summary_is_computed_correctly(client: AsyncClient, auth_headers):
    """summary fields are aggregated server-side across all items."""
    channel_id = await _create_channel(client, auth_headers, name="Ярмарка")
    p1 = await _create_product(client, auth_headers, name="А", stock_qty=2)
    p2 = await _create_product(client, auth_headers, name="Б", stock_qty=10)

    await client.post(f"/api/v1/fair-prep/{channel_id}/items", headers=auth_headers,
                      json={"product_id": p1, "planned_qty": 5})   # need_to_make=3
    res = await client.post(f"/api/v1/fair-prep/{channel_id}/items", headers=auth_headers,
                            json={"product_id": p2, "planned_qty": 4})  # need_to_make=0

    summary = res.json()["data"]["summary"]
    assert summary["total_positions"] == 2
    assert summary["total_planned"] == 9        # 5 + 4
    assert summary["total_need_to_make"] == 3   # 3 + 0


# ── user isolation ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_user_cannot_access_other_users_prep(
    client: AsyncClient, auth_headers, second_auth_headers
):
    channel_id = await _create_channel(client, auth_headers, name="Моя ярмарка")

    res = await client.get(f"/api/v1/fair-prep/{channel_id}", headers=second_auth_headers)
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_fair_channels_are_user_scoped(
    client: AsyncClient, auth_headers, second_auth_headers
):
    await _create_channel(client, auth_headers, name="Ярмарка пользователя 1")
    await _create_channel(client, second_auth_headers, name="Ярмарка пользователя 2")

    res = await client.get("/api/v1/fair-prep/channels", headers=auth_headers)
    names = [c["name"] for c in res.json()["data"]]
    assert "Ярмарка пользователя 1" in names
    assert "Ярмарка пользователя 2" not in names


# ── category and sale_price fields ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_item_includes_category_and_sale_price(client: AsyncClient, auth_headers):
    """Each item in the list exposes category and sale_price from the product."""
    channel_id = await _create_channel(client, auth_headers, name="Ярмарка")
    product_id = await _create_product(
        client, auth_headers, name="Мишка", sale_price="35.50", category="Вязаные игрушки"
    )
    res = await client.post(
        f"/api/v1/fair-prep/{channel_id}/items",
        headers=auth_headers,
        json={"product_id": product_id, "planned_qty": 3},
    )
    item = res.json()["data"]["items"][0]
    assert item["category"] == "Вязаные игрушки"
    assert float(item["sale_price"]) == 35.50


@pytest.mark.asyncio
async def test_item_category_none_when_not_set(client: AsyncClient, auth_headers):
    channel_id = await _create_channel(client, auth_headers, name="Ярмарка")
    product_id = await _create_product(client, auth_headers, name="Брелок")
    res = await client.post(
        f"/api/v1/fair-prep/{channel_id}/items",
        headers=auth_headers,
        json={"product_id": product_id, "planned_qty": 2},
    )
    assert res.json()["data"]["items"][0]["category"] is None


# ── category filter ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_category_filter_returns_only_matching_items(client: AsyncClient, auth_headers):
    channel_id = await _create_channel(client, auth_headers, name="Ярмарка")
    p1 = await _create_product(client, auth_headers, name="Мишка", category="Игрушки")
    p2 = await _create_product(client, auth_headers, name="Брелок", category="Аксессуары")

    for pid in (p1, p2):
        await client.post(f"/api/v1/fair-prep/{channel_id}/items", headers=auth_headers,
                          json={"product_id": pid, "planned_qty": 2})

    res = await client.get(
        f"/api/v1/fair-prep/{channel_id}",
        headers=auth_headers,
        params={"category": "Игрушки"},
    )
    assert res.status_code == 200
    items = res.json()["data"]["items"]
    assert len(items) == 1
    assert items[0]["product_name"] == "Мишка"


@pytest.mark.asyncio
async def test_category_filter_does_not_affect_summary_positions(client: AsyncClient, auth_headers):
    """Summary reflects only filtered items."""
    channel_id = await _create_channel(client, auth_headers, name="Ярмарка")
    p1 = await _create_product(client, auth_headers, name="А", category="Кат1")
    p2 = await _create_product(client, auth_headers, name="Б", category="Кат2")

    for pid, qty in ((p1, 3), (p2, 5)):
        await client.post(f"/api/v1/fair-prep/{channel_id}/items", headers=auth_headers,
                          json={"product_id": pid, "planned_qty": qty})

    res = await client.get(
        f"/api/v1/fair-prep/{channel_id}", headers=auth_headers, params={"category": "Кат1"},
    )
    summary = res.json()["data"]["summary"]
    assert summary["total_positions"] == 1
    assert summary["total_planned"] == 3


# ── sort_by ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_sort_by_price_asc(client: AsyncClient, auth_headers):
    channel_id = await _create_channel(client, auth_headers, name="Ярмарка")
    p_cheap = await _create_product(client, auth_headers, name="Дешёвое", sale_price="10.00")
    p_mid   = await _create_product(client, auth_headers, name="Среднее",  sale_price="25.00")
    p_pricey = await _create_product(client, auth_headers, name="Дорогое", sale_price="50.00")

    for pid in (p_pricey, p_cheap, p_mid):
        await client.post(f"/api/v1/fair-prep/{channel_id}/items", headers=auth_headers,
                          json={"product_id": pid, "planned_qty": 1})

    res = await client.get(
        f"/api/v1/fair-prep/{channel_id}", headers=auth_headers, params={"sort_by": "price_asc"},
    )
    prices = [float(i["sale_price"]) for i in res.json()["data"]["items"]]
    assert prices == sorted(prices)


@pytest.mark.asyncio
async def test_sort_by_price_desc(client: AsyncClient, auth_headers):
    channel_id = await _create_channel(client, auth_headers, name="Ярмарка")
    for name, price in (("А", "5.00"), ("Б", "30.00"), ("В", "15.00")):
        pid = await _create_product(client, auth_headers, name=name, sale_price=price)
        await client.post(f"/api/v1/fair-prep/{channel_id}/items", headers=auth_headers,
                          json={"product_id": pid, "planned_qty": 1})

    res = await client.get(
        f"/api/v1/fair-prep/{channel_id}", headers=auth_headers, params={"sort_by": "price_desc"},
    )
    prices = [float(i["sale_price"]) for i in res.json()["data"]["items"]]
    assert prices == sorted(prices, reverse=True)


@pytest.mark.asyncio
async def test_sort_by_category(client: AsyncClient, auth_headers):
    channel_id = await _create_channel(client, auth_headers, name="Ярмарка")
    for name, cat in (("Зайка", "Игрушки"), ("Брелок", "Аксессуары"), ("Мишка", "Игрушки")):
        pid = await _create_product(client, auth_headers, name=name, category=cat)
        await client.post(f"/api/v1/fair-prep/{channel_id}/items", headers=auth_headers,
                          json={"product_id": pid, "planned_qty": 1})

    res = await client.get(
        f"/api/v1/fair-prep/{channel_id}", headers=auth_headers, params={"sort_by": "category"},
    )
    items = res.json()["data"]["items"]
    # Аксессуары before Игрушки alphabetically, within Игрушки: Зайка before Мишка
    assert items[0]["category"] == "Аксессуары"
    assert items[1]["product_name"] == "Зайка"
    assert items[2]["product_name"] == "Мишка"


@pytest.mark.asyncio
async def test_invalid_sort_by_returns_422(client: AsyncClient, auth_headers):
    channel_id = await _create_channel(client, auth_headers, name="Ярмарка")
    res = await client.get(
        f"/api/v1/fair-prep/{channel_id}", headers=auth_headers, params={"sort_by": "invalid"},
    )
    assert res.status_code == 422


@pytest.mark.asyncio
async def test_filter_and_sort_passed_through_on_mutation(client: AsyncClient, auth_headers):
    """Mutating endpoints respect category + sort_by and return consistently filtered list."""
    channel_id = await _create_channel(client, auth_headers, name="Ярмарка")
    p1 = await _create_product(client, auth_headers, name="Зайка", category="Игрушки", sale_price="20.00")
    p2 = await _create_product(client, auth_headers, name="Брелок", category="Аксессуары", sale_price="10.00")
    p3 = await _create_product(client, auth_headers, name="Мишка", category="Игрушки", sale_price="15.00")

    for pid in (p1, p2):
        await client.post(f"/api/v1/fair-prep/{channel_id}/items", headers=auth_headers,
                          json={"product_id": pid, "planned_qty": 1})

    # add p3 with filter+sort active — response should only show Игрушки, sorted by price_asc
    res = await client.post(
        f"/api/v1/fair-prep/{channel_id}/items",
        headers=auth_headers,
        params={"category": "Игрушки", "sort_by": "price_asc"},
        json={"product_id": p3, "planned_qty": 2},
    )
    assert res.status_code == 201
    items = res.json()["data"]["items"]
    names = [i["product_name"] for i in items]
    assert "Брелок" not in names                    # filtered out
    assert names == ["Мишка", "Зайка"]              # price_asc: 15 before 20
