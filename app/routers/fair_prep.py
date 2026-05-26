from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy import asc, desc
from app.database import get_db
from app.models.user import User
from app.models.product import Product
from app.models.sales_channel import SalesChannel
from app.models.fair_item import FairItem
from app.schemas.fair_prep import (
    FairItemAdd, FairItemUpdate,
    FairItemOut, FairChannelRef, FairPrepOut, FairPrepSummary,
)
from app.auth.dependencies import get_current_user

router = APIRouter(
    prefix="/fair-prep",
    tags=["fair-prep"],
    dependencies=[Depends(get_current_user)],
)

_SORT_OPTIONS = {
    "name":       asc(Product.name),
    "category":   (asc(Product.category), asc(Product.name)),
    "price_asc":  (asc(Product.sale_price), asc(Product.name)),
    "price_desc": (desc(Product.sale_price), asc(Product.name)),
}


async def _get_channel(channel_id, user: User, db: AsyncSession) -> SalesChannel:
    result = await db.execute(
        select(SalesChannel).where(
            (SalesChannel.id == channel_id) & (SalesChannel.user_id == user.id)
        )
    )
    channel = result.scalars().first()
    if not channel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found")
    return channel


async def _get_item(item_id, channel_id, user: User, db: AsyncSession) -> FairItem:
    result = await db.execute(
        select(FairItem).where(
            (FairItem.id == item_id)
            & (FairItem.channel_id == channel_id)
            & (FairItem.user_id == user.id)
        )
    )
    item = result.scalars().first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return item


async def _load_items(
    channel_id,
    user: User,
    db: AsyncSession,
    category: Optional[str],
    sort_by: Optional[str],
) -> list[FairItem]:
    order = _SORT_OPTIONS.get(sort_by or "name", asc(Product.name))
    order_clauses = order if isinstance(order, tuple) else (order,)

    query = (
        select(FairItem)
        .join(Product, FairItem.product_id == Product.id)
        .options(selectinload(FairItem.product))
        .where((FairItem.channel_id == channel_id) & (FairItem.user_id == user.id))
    )
    if category:
        query = query.where(Product.category == category)

    for clause in order_clauses:
        query = query.order_by(clause)

    result = await db.execute(query)
    return result.scalars().all()


def _build_item_out(item: FairItem) -> FairItemOut:
    stock = item.product.stock_qty
    return FairItemOut(
        id=item.id,
        product_id=item.product_id,
        product_name=item.product.name,
        category=item.product.category,
        sale_price=item.product.sale_price,
        planned_qty=item.planned_qty,
        stock_qty=stock,
        need_to_make=max(0, item.planned_qty - stock),
    )


def _build_prep_out(channel: SalesChannel, items: list[FairItem]) -> FairPrepOut:
    items_out = [_build_item_out(i) for i in items]
    return FairPrepOut(
        channel=FairChannelRef(
            id=channel.id,
            name=channel.name,
            event_date=channel.event_date,
            location=channel.location,
        ),
        items=items_out,
        summary=FairPrepSummary(
            total_positions=len(items_out),
            total_planned=sum(i.planned_qty for i in items_out),
            total_need_to_make=sum(i.need_to_make for i in items_out),
        ),
    )


@router.get("/channels", response_model=dict)
async def list_fair_channels(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all channels of type 'ярмарка' for the current user."""
    result = await db.execute(
        select(SalesChannel)
        .where((SalesChannel.user_id == user.id) & (SalesChannel.type == "ярмарка"))
        .order_by(SalesChannel.event_date.desc().nullslast(), SalesChannel.created_at.desc())
    )
    channels = result.scalars().all()
    return {"data": [
        FairChannelRef(id=c.id, name=c.name, event_date=c.event_date, location=c.location)
        for c in channels
    ]}


@router.get("/{channel_id}", response_model=dict)
async def get_fair_prep(
    channel_id,
    category: Optional[str] = Query(None),
    sort_by: Optional[str] = Query(None, pattern="^(name|category|price_asc|price_desc)$"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the preparation list with optional category filter and sort."""
    channel = await _get_channel(channel_id, user, db)
    items = await _load_items(channel_id, user, db, category, sort_by)
    return {"data": _build_prep_out(channel, items)}


@router.post("/{channel_id}/items", response_model=dict, status_code=status.HTTP_201_CREATED)
async def add_item(
    channel_id,
    body: FairItemAdd,
    category: Optional[str] = Query(None),
    sort_by: Optional[str] = Query(None, pattern="^(name|category|price_asc|price_desc)$"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a product to the list. Returns the updated list with current filter/sort."""
    channel = await _get_channel(channel_id, user, db)

    existing = await db.execute(
        select(FairItem).where(
            (FairItem.channel_id == channel_id) & (FairItem.product_id == body.product_id)
        )
    )
    if existing.scalars().first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Product already in the list")

    db.add(FairItem(
        user_id=user.id,
        channel_id=channel_id,
        product_id=body.product_id,
        planned_qty=body.planned_qty,
    ))
    await db.commit()

    items = await _load_items(channel_id, user, db, category, sort_by)
    return {"data": _build_prep_out(channel, items)}


@router.put("/{channel_id}/items/{item_id}", response_model=dict)
async def update_item(
    channel_id,
    item_id,
    body: FairItemUpdate,
    category: Optional[str] = Query(None),
    sort_by: Optional[str] = Query(None, pattern="^(name|category|price_asc|price_desc)$"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update planned quantity. Returns the updated list with current filter/sort."""
    channel = await _get_channel(channel_id, user, db)
    item = await _get_item(item_id, channel_id, user, db)
    item.planned_qty = body.planned_qty
    await db.commit()

    items = await _load_items(channel_id, user, db, category, sort_by)
    return {"data": _build_prep_out(channel, items)}


@router.delete("/{channel_id}/items/{item_id}", response_model=dict)
async def remove_item(
    channel_id,
    item_id,
    category: Optional[str] = Query(None),
    sort_by: Optional[str] = Query(None, pattern="^(name|category|price_asc|price_desc)$"),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a product from the list. Returns the updated list with current filter/sort."""
    channel = await _get_channel(channel_id, user, db)
    item = await _get_item(item_id, channel_id, user, db)
    await db.delete(item)
    await db.commit()

    items = await _load_items(channel_id, user, db, category, sort_by)
    return {"data": _build_prep_out(channel, items)}
