from typing import Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_
from sqlalchemy.orm import selectinload
from app.database import get_db
from app.models.user import User
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.models.product import Product
from app.schemas.sale import (
    SaleCreate,
    SaleUpdate,
    SaleOut,
    SaleDetailOut,
    SaleItemOut,
)
from app.auth.dependencies import get_current_user
from app.services.sale import calc_sale_total_amount

router = APIRouter(
    prefix="/sales",
    tags=["sales"],
    dependencies=[Depends(get_current_user)],
)


async def _get_sale(sale_id, user: User, db: AsyncSession) -> Sale:
    """Get sale and verify ownership"""
    result = await db.execute(
        select(Sale).where(
            (Sale.id == sale_id) & (Sale.user_id == user.id)
        )
    )
    sale = result.scalars().first()
    if not sale:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Sale not found",
        )
    return sale


def _enrich_sale(sale: Sale) -> SaleOut:
    """Enrich sale with calculated fields"""
    total_amount = calc_sale_total_amount(sale)
    return SaleOut(
        **sale.__dict__,
        total_amount=total_amount,
    )


@router.get("", response_model=dict)
async def list_sales(
    buyer_id: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all sales for current user"""
    query = select(Sale).options(selectinload(Sale.items)).where(Sale.user_id == user.id)

    if buyer_id:
        query = query.where(Sale.buyer_id == buyer_id)

    if date_from:
        query = query.where(Sale.sale_date >= date_from)

    if date_to:
        query = query.where(Sale.sale_date <= date_to)

    result = await db.execute(query)
    sales = result.scalars().all()

    enriched = [_enrich_sale(s) for s in sales]
    return {"data": enriched, "meta": {"total": len(enriched)}}


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_sale(
    sale_create: SaleCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new sale"""
    # Create sale
    new_sale = Sale(
        user_id=user.id,
        buyer_id=sale_create.buyer_id,
        sale_date=sale_create.sale_date,
        notes=sale_create.notes,
    )

    db.add(new_sale)
    await db.flush()  # Get the ID without committing

    # Add sale items and update stock
    for item_data in sale_create.items:
        sale_item = SaleItem(
            user_id=user.id,
            sale_id=new_sale.id,
            product_id=item_data.product_id,
            quantity=item_data.quantity,
            price=item_data.price,
        )
        db.add(sale_item)

        # Update product stock
        if item_data.product_id:
            product_result = await db.execute(
                select(Product).where(Product.id == item_data.product_id)
            )
            product = product_result.scalars().first()
            if product:
                product.stock_qty -= item_data.quantity

    await db.commit()

    result = await db.execute(
        select(Sale).options(selectinload(Sale.items)).where(Sale.id == new_sale.id)
    )
    new_sale = result.scalars().first()

    return {"data": _enrich_sale(new_sale)}


@router.get("/{sale_id}", response_model=dict)
async def get_sale(
    sale_id,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get sale details"""
    sale = await _get_sale(sale_id, user, db)

    # Load items
    items_result = await db.execute(
        select(SaleItem).where(SaleItem.sale_id == sale.id)
    )
    items = items_result.scalars().all()

    # Enrich items with product names
    enriched_items = []
    for item in items:
        product_name = None
        if item.product_id:
            prod_result = await db.execute(
                select(Product).where(Product.id == item.product_id)
            )
            product = prod_result.scalars().first()
            product_name = product.name if product else None

        enriched_items.append(
            SaleItemOut(
                id=item.id,
                sale_id=item.sale_id,
                product_id=item.product_id,
                quantity=item.quantity,
                price=item.price,
                product_name=product_name,
            )
        )

    total_amount = calc_sale_total_amount(sale)

    # Get buyer name if exists
    buyer_name = None
    if sale.buyer_id:
        from app.models.buyer import Buyer
        buyer_result = await db.execute(
            select(Buyer).where(Buyer.id == sale.buyer_id)
        )
        buyer = buyer_result.scalars().first()
        buyer_name = buyer.name if buyer else None

    sale_detail = SaleDetailOut(
        **SaleOut(
            **sale.__dict__,
            total_amount=total_amount,
        ).model_dump(),
        items=enriched_items,
        buyer_name=buyer_name,
    )

    return {"data": sale_detail}


@router.put("/{sale_id}", response_model=dict)
async def update_sale(
    sale_id,
    sale_update: SaleUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a sale (limited fields)"""
    sale = await _get_sale(sale_id, user, db)

    update_data = sale_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(sale, key, value)

    await db.commit()

    result = await db.execute(
        select(Sale).options(selectinload(Sale.items)).where(Sale.id == sale.id)
    )
    sale = result.scalars().first()

    return {"data": _enrich_sale(sale)}


@router.delete("/{sale_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_sale(
    sale_id,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a sale"""
    sale = await _get_sale(sale_id, user, db)

    # Restore product stock
    items_result = await db.execute(
        select(SaleItem).where(SaleItem.sale_id == sale.id)
    )
    items = items_result.scalars().all()

    for item in items:
        if item.product_id:
            product_result = await db.execute(
                select(Product).where(Product.id == item.product_id)
            )
            product = product_result.scalars().first()
            if product:
                product.stock_qty += item.quantity

    await db.delete(sale)
    await db.commit()
