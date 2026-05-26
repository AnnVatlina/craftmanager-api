from typing import Optional
from datetime import date
from decimal import Decimal
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func, desc
from app.database import get_db
from app.models.user import User
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.models.expense import Expense
from app.models.product import Product
from app.models.material_purchase import MaterialPurchase
from app.auth.dependencies import get_current_user

router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"],
    dependencies=[Depends(get_current_user)],
)


@router.get("/summary", response_model=dict)
async def get_summary(
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get financial summary"""
    # Calculate total revenue from sales
    sales_query = select(func.sum(SaleItem.quantity * SaleItem.price)).join(
        Sale
    ).where(Sale.user_id == user.id)

    if date_from:
        sales_query = sales_query.where(Sale.sale_date >= date_from)
    if date_to:
        sales_query = sales_query.where(Sale.sale_date <= date_to)

    sales_result = await db.execute(sales_query)
    total_revenue = sales_result.scalar() or Decimal("0")

    # Calculate total expenses
    expenses_query = select(func.sum(Expense.amount)).where(Expense.user_id == user.id)

    if date_from:
        expenses_query = expenses_query.where(Expense.expense_date >= date_from)
    if date_to:
        expenses_query = expenses_query.where(Expense.expense_date <= date_to)

    expenses_result = await db.execute(expenses_query)
    manual_expenses = expenses_result.scalar() or Decimal("0")

    # Material purchase costs
    material_query = select(func.sum(MaterialPurchase.total_cost)).where(
        MaterialPurchase.user_id == user.id
    )
    if date_from:
        material_query = material_query.where(MaterialPurchase.purchased_at >= date_from)
    if date_to:
        material_query = material_query.where(MaterialPurchase.purchased_at <= date_to)
    material_result = await db.execute(material_query)
    material_expenses = material_result.scalar() or Decimal("0")

    total_expenses = manual_expenses + material_expenses
    profit = total_revenue - total_expenses

    return {
        "data": {
            "total_revenue": total_revenue,
            "total_expenses": total_expenses,
            "manual_expenses": manual_expenses,
            "material_expenses": material_expenses,
            "profit": profit,
        }
    }


@router.get("/top-products", response_model=dict)
async def get_top_products(
    limit: int = 10,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get top products by revenue"""
    query = (
        select(
            SaleItem.product_id,
            Product.name.label("product_name"),
            func.sum(SaleItem.quantity * SaleItem.price).label("revenue"),
            func.sum(SaleItem.quantity).label("quantity"),
        )
        .join(Sale, SaleItem.sale_id == Sale.id)
        .outerjoin(Product, SaleItem.product_id == Product.id)
        .where(Sale.user_id == user.id)
        .group_by(SaleItem.product_id, Product.name)
    )

    if date_from:
        query = query.where(Sale.sale_date >= date_from)
    if date_to:
        query = query.where(Sale.sale_date <= date_to)

    query = query.order_by(desc("revenue")).limit(limit)

    result = await db.execute(query)
    rows = result.all()

    return {"data": [
        {"product_id": r.product_id, "product_name": r.product_name, "revenue": r.revenue, "quantity": r.quantity}
        for r in rows if r.product_id
    ]}


@router.get("/low-stock", response_model=dict)
async def get_low_stock(
    threshold: int = 5,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get products with low stock"""
    query = select(Product).where(
        (Product.user_id == user.id) & (Product.stock_qty <= threshold)
    ).order_by(Product.stock_qty)

    result = await db.execute(query)
    products = result.scalars().all()

    return {
        "data": [
            {
                "id": p.id,
                "name": p.name,
                "stock_qty": p.stock_qty,
                "category": p.category,
            }
            for p in products
        ]
    }
