from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models.user import User
from app.models.buyer import Buyer
from app.models.sale import Sale
from app.schemas.buyer import BuyerCreate, BuyerUpdate, BuyerOut
from app.auth.dependencies import get_current_user

router = APIRouter(
    prefix="/buyers",
    tags=["buyers"],
    dependencies=[Depends(get_current_user)],
)


async def _get_buyer(buyer_id, user: User, db: AsyncSession) -> Buyer:
    """Get buyer and verify ownership"""
    result = await db.execute(
        select(Buyer).where(
            (Buyer.id == buyer_id) & (Buyer.user_id == user.id)
        )
    )
    buyer = result.scalars().first()
    if not buyer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Buyer not found",
        )
    return buyer


@router.get("", response_model=dict)
async def list_buyers(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all buyers for current user"""
    result = await db.execute(
        select(Buyer).where(Buyer.user_id == user.id)
    )
    buyers = result.scalars().all()
    return {"data": [BuyerOut.model_validate(b) for b in buyers], "meta": {"total": len(buyers)}}


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_buyer(
    buyer_create: BuyerCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new buyer"""
    new_buyer = Buyer(
        user_id=user.id,
        name=buyer_create.name,
        contact=buyer_create.contact,
        notes=buyer_create.notes,
    )

    db.add(new_buyer)
    await db.commit()
    await db.refresh(new_buyer)

    return {"data": BuyerOut.model_validate(new_buyer)}


@router.get("/{buyer_id}", response_model=dict)
async def get_buyer(
    buyer_id,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get buyer details with purchase history"""
    buyer = await _get_buyer(buyer_id, user, db)

    # Get buyer's sales
    sales_result = await db.execute(
        select(Sale).where(Sale.buyer_id == buyer_id)
    )
    sales = sales_result.scalars().all()

    return {
        "data": {
            **BuyerOut.model_validate(buyer).model_dump(),
            "sales_count": len(sales),
        }
    }


@router.put("/{buyer_id}", response_model=dict)
async def update_buyer(
    buyer_id,
    buyer_update: BuyerUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a buyer"""
    buyer = await _get_buyer(buyer_id, user, db)

    update_data = buyer_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(buyer, key, value)

    await db.commit()
    await db.refresh(buyer)

    return {"data": BuyerOut.model_validate(buyer)}


@router.delete("/{buyer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_buyer(
    buyer_id,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a buyer"""
    buyer = await _get_buyer(buyer_id, user, db)
    await db.delete(buyer)
    await db.commit()
