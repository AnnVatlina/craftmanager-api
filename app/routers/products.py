import math
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from app.database import get_db
from app.models.user import User
from app.models.product import Product
from app.models.product_material import ProductMaterial
from app.models.material import Material
from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductOut,
    ProductDetailOut,
    ProductMaterialItemCreate,
    ProductMaterialItemOut,
)
from app.auth.dependencies import get_current_user
from app.services.product import calc_product_cost_price

router = APIRouter(
    prefix="/products",
    tags=["products"],
    dependencies=[Depends(get_current_user)],
)


def _enrich_product(product: Product, cost_price: Optional = None) -> ProductOut:
    """Enrich product with calculated fields"""
    return ProductOut(
        **product.__dict__,
        cost_price=cost_price,
    )


async def _get_product(
    product_id, user: User, db: AsyncSession
) -> Product:
    """Get product and verify ownership"""
    result = await db.execute(
        select(Product).where(
            (Product.id == product_id) & (Product.user_id == user.id)
        )
    )
    product = result.scalars().first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found",
        )
    return product


@router.get("", response_model=dict)
async def list_products(
    category: Optional[str] = None,
    in_stock: Optional[bool] = None,
    page: int = 1,
    per_page: int = 20,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List all products for current user with pagination"""
    def _apply_filters(q):
        if category:
            q = q.where(Product.category == category)
        if in_stock is not None:
            q = q.where(Product.stock_qty > 0) if in_stock else q.where(Product.stock_qty == 0)
        return q

    agg_query = _apply_filters(
        select(
            func.count(Product.id),
            func.coalesce(func.sum(Product.stock_qty * Product.sale_price), 0),
        ).where(Product.user_id == user.id)
    )
    agg_result = await db.execute(agg_query)
    total, total_stock_value = agg_result.first()

    offset = (page - 1) * per_page
    page_query = _apply_filters(
        select(Product).where(Product.user_id == user.id)
    ).order_by(Product.created_at.desc()).offset(offset).limit(per_page)

    result = await db.execute(page_query)
    products = result.scalars().all()

    enriched = []
    for product in products:
        cost_price = await calc_product_cost_price(db, product)
        enriched.append(_enrich_product(product, cost_price))

    return {
        "data": enriched,
        "meta": {
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": math.ceil(total / per_page) if total else 1,
            "total_stock_value": total_stock_value,
        },
    }


@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_create: ProductCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new product"""
    new_product = Product(
        user_id=user.id,
        name=product_create.name,
        description=product_create.description,
        category=product_create.category,
        sale_price=product_create.sale_price,
        stock_qty=product_create.stock_qty or 0,
    )

    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)

    cost_price = await calc_product_cost_price(db, new_product)
    return {"data": _enrich_product(new_product, cost_price)}


@router.get("/{product_id}", response_model=dict)
async def get_product(
    product_id,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get product details with materials"""
    product = await _get_product(product_id, user, db)

    # Load materials
    result = await db.execute(
        select(ProductMaterial).where(ProductMaterial.product_id == product.id)
    )
    materials = result.scalars().all()

    cost_price = await calc_product_cost_price(db, product)

    # Enrich materials info
    enriched_materials = []
    for pm in materials:
        mat_result = await db.execute(
            select(Material).where(Material.id == pm.material_id)
        )
        material = mat_result.scalars().first()

        enriched_materials.append(
            ProductMaterialItemOut(
                id=pm.id,
                material_id=pm.material_id,
                product_id=pm.product_id,
                quantity=pm.quantity,
                material_name=material.name if material else None,
                material_unit=material.unit if material else None,
                material_price=material.price_per_unit if material else None,
            )
        )

    product_detail = ProductDetailOut(
        **ProductOut(
            **product.__dict__,
            cost_price=cost_price,
        ).model_dump(),
        materials=enriched_materials,
    )

    return {"data": product_detail}


@router.put("/{product_id}", response_model=dict)
async def update_product(
    product_id,
    product_update: ProductUpdate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a product"""
    product = await _get_product(product_id, user, db)

    update_data = product_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(product, key, value)

    await db.commit()
    await db.refresh(product)

    cost_price = await calc_product_cost_price(db, product)
    return {"data": _enrich_product(product, cost_price)}


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a product"""
    product = await _get_product(product_id, user, db)
    await db.delete(product)
    await db.commit()


@router.get("/{product_id}/materials", response_model=dict)
async def get_product_materials(
    product_id,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get materials for a product"""
    product = await _get_product(product_id, user, db)

    result = await db.execute(
        select(ProductMaterial).where(ProductMaterial.product_id == product.id)
    )
    product_materials = result.scalars().all()

    enriched_materials = []
    for pm in product_materials:
        mat_result = await db.execute(
            select(Material).where(Material.id == pm.material_id)
        )
        material = mat_result.scalars().first()

        enriched_materials.append(
            ProductMaterialItemOut(
                id=pm.id,
                material_id=pm.material_id,
                product_id=pm.product_id,
                quantity=pm.quantity,
                material_name=material.name if material else None,
                material_unit=material.unit if material else None,
                material_price=material.price_per_unit if material else None,
            )
        )

    return {"data": enriched_materials}


@router.post("/{product_id}/materials", response_model=dict, status_code=status.HTTP_201_CREATED)
async def add_product_material(
    product_id,
    material_item: ProductMaterialItemCreate,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Add a material to a product's composition"""
    product = await _get_product(product_id, user, db)

    # Check if material exists and belongs to user
    mat_result = await db.execute(
        select(Material).where(
            (Material.id == material_item.material_id) & (Material.user_id == user.id)
        )
    )
    material = mat_result.scalars().first()

    if not material:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Material not found",
        )

    # Check if this material is already in the product
    existing_result = await db.execute(
        select(ProductMaterial).where(
            (ProductMaterial.product_id == product_id)
            & (ProductMaterial.material_id == material_item.material_id)
        )
    )
    existing = existing_result.scalars().first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Material already in product",
        )

    # Create product material
    pm = ProductMaterial(
        user_id=user.id,
        product_id=product_id,
        material_id=material_item.material_id,
        quantity=material_item.quantity,
    )

    db.add(pm)
    await db.commit()
    await db.refresh(pm)

    return {
        "data": ProductMaterialItemOut(
            id=pm.id,
            material_id=pm.material_id,
            product_id=pm.product_id,
            quantity=pm.quantity,
            material_name=material.name,
            material_unit=material.unit,
            material_price=material.price_per_unit,
        )
    }


@router.delete("/{product_id}/materials/{material_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_product_material(
    product_id,
    material_id,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Remove a material from a product's composition"""
    product = await _get_product(product_id, user, db)

    result = await db.execute(
        select(ProductMaterial).where(
            (ProductMaterial.product_id == product_id)
            & (ProductMaterial.material_id == material_id)
            & (ProductMaterial.user_id == user.id)
        )
    )
    pm = result.scalars().first()

    if not pm:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product material not found",
        )

    await db.delete(pm)
    await db.commit()
