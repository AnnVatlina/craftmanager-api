from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models import Product, ProductMaterial


async def calc_product_cost_price(
    db: AsyncSession, product: Product
) -> Decimal:
    """Calculate the cost price of a product from its materials"""
    # Load relationships if not already loaded
    if not product.materials:
        result = await db.execute(
            select(ProductMaterial)
            .where(ProductMaterial.product_id == product.id)
        )
        materials = result.scalars().all()
    else:
        materials = product.materials

    total_cost = Decimal("0")
    for pm in materials:
        # Need to ensure material is loaded
        if not pm.material:
            result = await db.execute(
                select(ProductMaterial).where(ProductMaterial.id == pm.id)
            )
            pm = result.scalars().first()
        
        cost = pm.quantity * pm.material.price_per_unit
        total_cost += cost

    return total_cost


def calc_sale_total_amount(sale) -> Decimal:
    """Calculate the total amount of a sale from its items"""
    total = Decimal("0")
    for item in sale.items:
        total += item.quantity * item.price
    return total
