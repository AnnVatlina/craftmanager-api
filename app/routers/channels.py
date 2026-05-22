from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models.user import User
from app.models.sales_channel import SalesChannel
from app.models.sale import Sale
from app.schemas.sales_channel import (
    SalesChannelCreate, SalesChannelUpdate, SalesChannelOut,
    SalesChannelDetailOut, ChannelSaleOut,
)
from app.auth.dependencies import get_current_user

router = APIRouter(
    prefix="/channels",
    tags=["channels"],
    dependencies=[Depends(get_current_user)],
)


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


@router.get("", response_model=dict)
async def list_channels(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(SalesChannel).where(SalesChannel.user_id == user.id))
    channels = result.scalars().all()
    return {"data": [SalesChannelOut.model_validate(c) for c in channels], "meta": {"total": len(channels)}}


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_channel(
    body: SalesChannelCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    channel = SalesChannel(user_id=user.id, **body.model_dump())
    db.add(channel)
    await db.commit()
    await db.refresh(channel)
    return {"data": SalesChannelOut.model_validate(channel)}


@router.get("/{channel_id}", response_model=dict)
async def get_channel(
    channel_id,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    channel = await _get_channel(channel_id, user, db)
    result = await db.execute(
        select(Sale).options(selectinload(Sale.items))
        .where((Sale.channel_id == channel_id) & (Sale.user_id == user.id))
    )
    sales = result.scalars().all()
    sale_list = [
        ChannelSaleOut(
            id=s.id,
            sale_date=s.sale_date,
            notes=s.notes,
            total_amount=sum((i.quantity * i.price for i in s.items), Decimal("0")),
        )
        for s in sales
    ]
    detail = SalesChannelDetailOut(
        **SalesChannelOut.model_validate(channel).model_dump(),
        sales=sale_list,
        sales_count=len(sale_list),
    )
    return {"data": detail}


@router.put("/{channel_id}", response_model=dict)
async def update_channel(
    channel_id,
    body: SalesChannelUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    channel = await _get_channel(channel_id, user, db)
    for key, value in body.model_dump(exclude_unset=True).items():
        setattr(channel, key, value)
    await db.commit()
    await db.refresh(channel)
    return {"data": SalesChannelOut.model_validate(channel)}


@router.delete("/{channel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_channel(
    channel_id,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    channel = await _get_channel(channel_id, user, db)
    await db.delete(channel)
    await db.commit()
