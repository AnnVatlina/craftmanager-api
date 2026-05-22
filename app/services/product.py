from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models import Product, ProductMaterial
from app.models.material import Material


async def calc_product_cost_price(
    db: AsyncSession, product: Product
) -> Decimal:
    """Calculate the cost price of a product from its materials via a single JOIN query"""
    result = await db.execute(
        select(ProductMaterial.quantity, Material.price_per_unit)
        .join(Material, ProductMaterial.material_id == Material.id)
        .where(ProductMaterial.product_id == product.id)
    )
    rows = result.all()
    total = sum((row.quantity * row.price_per_unit for row in rows), Decimal("0"))
    return total.quantize(Decimal("0.01"))
