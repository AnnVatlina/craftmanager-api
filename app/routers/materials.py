from typing import Optional
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models.user import User
from app.models.material import Material
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
    new_material = Material(
        user_id=user.id,
        name=material_create.name,
        unit=material_create.unit,
        price_per_unit=material_create.price_per_unit,
        stock_qty=material_create.stock_qty or 0,
    )

    db.add(new_material)
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

    material.stock_qty += restock.qty
    if restock.price_per_unit:
        material.price_per_unit = restock.price_per_unit

    await db.commit()
    await db.refresh(material)

    return {"data": MaterialOut.model_validate(material)}
