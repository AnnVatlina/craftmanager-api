from typing import Optional
from decimal import Decimal
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models.user import User
from app.models.material import Material
from app.models.material_purchase import MaterialPurchase
from app.schemas.material import (
    MaterialCreate,
    MaterialUpdate,
    MaterialOut,
    MaterialRestockRequest,
)
from app.auth.dependencies import get_current_user

router = APIRouter(
    prefix="/materials",
    tags=["materials"],
    dependencies=[Depends(get_current_user)],
)


async def _get_material(material_id, user: User, db: AsyncSession) -> Material:
    """Get material and verify ownership"""
    result = await db.execute(
        select(Material).where(
            (Material.id == material_id) & (Material.user_id == user.id)
        )
    )
    material = result.scalars().first()
    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found",
        )
    return material


@router.get("", response_model=dict)
async def list_materials(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all materials for current user"""
    result = await db.execute(
        select(Material).where(Material.user_id == user.id)
    )
    materials = result.scalars().all()
    return {"data": [MaterialOut.model_validate(m) for m in materials], "meta": {"total": len(materials)}}


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_material(
    material_create: MaterialCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new material"""
    qty = material_create.stock_qty or Decimal("0")
    new_material = Material(
        user_id=user.id,
        name=material_create.name,
        unit=material_create.unit,
        price_per_unit=material_create.price_per_unit,
        stock_qty=qty,
    )
    db.add(new_material)
    await db.flush()

    if qty > 0:
        db.add(MaterialPurchase(
            user_id=user.id,
            material_id=new_material.id,
            purchased_at=date.today(),
            quantity=qty,
            price_per_unit=material_create.price_per_unit,
            total_cost=(qty * material_create.price_per_unit).quantize(Decimal("0.01")),
        ))

    await db.commit()
    await db.refresh(new_material)

    return {"data": MaterialOut.model_validate(new_material)}


@router.get("/{material_id}", response_model=dict)
async def get_material(
    material_id,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get material details"""
    material = await _get_material(material_id, user, db)
    return {"data": MaterialOut.model_validate(material)}


@router.put("/{material_id}", response_model=dict)
async def update_material(
    material_id,
    material_update: MaterialUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a material"""
    material = await _get_material(material_id, user, db)

    update_data = material_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(material, key, value)

    await db.commit()
    await db.refresh(material)

    return {"data": MaterialOut.model_validate(material)}


@router.delete("/{material_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_material(
    material_id,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a material"""
    material = await _get_material(material_id, user, db)
    await db.delete(material)
    await db.commit()


@router.post("/{material_id}/restock", response_model=dict)
async def restock_material(
    material_id,
    restock: MaterialRestockRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Restock a material"""
    material = await _get_material(material_id, user, db)

    price = restock.price_per_unit or material.price_per_unit

    if restock.price_per_unit:
        if material.stock_qty > 0:
            old_total = material.stock_qty * material.price_per_unit
            new_total = restock.qty * restock.price_per_unit
            new_price = (old_total + new_total) / (material.stock_qty + restock.qty)
            material.price_per_unit = new_price.quantize(Decimal("0.0001"))
        else:
            material.price_per_unit = restock.price_per_unit
    material.stock_qty += restock.qty

    db.add(MaterialPurchase(
        user_id=user.id,
        material_id=material.id,
        purchased_at=restock.purchased_at or date.today(),
        quantity=restock.qty,
        price_per_unit=price,
        total_cost=(restock.qty * price).quantize(Decimal("0.01")),
    ))

    await db.commit()
    await db.refresh(material)

    return {"data": MaterialOut.model_validate(material)}
