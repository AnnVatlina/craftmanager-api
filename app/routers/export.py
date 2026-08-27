import csv
import io
import zipfile
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models.user import User
from app.models.product import Product
from app.models.material import Material
from app.models.product_material import ProductMaterial
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.models.sales_channel import SalesChannel
from app.models.material_purchase import MaterialPurchase
from app.models.product_production import ProductProduction
from app.models.expense import Expense
from app.models.buyer import Buyer
from app.models.fair_item import FairItem
from app.models.user_setting import UserSetting
from app.auth.dependencies import get_current_user

router = APIRouter(
    prefix="/export",
    tags=["export"],
    dependencies=[Depends(get_current_user)],
)


def _make_csv(fieldnames: list[str], rows: list[dict]) -> str:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue()


@router.get("/csv")
async def export_all_csv(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    uid = user.id

    async def fetch(model):
        result = await db.execute(select(model).where(model.user_id == uid))
        return result.scalars().all()

    settings_result = await db.execute(
        select(UserSetting).where(UserSetting.user_id == uid)
    )
    user_settings = settings_result.scalars().all()

    products = await fetch(Product)
    materials = await fetch(Material)
    product_materials = await fetch(ProductMaterial)
    channels = await fetch(SalesChannel)
    sales = await fetch(Sale)
    sale_items = await fetch(SaleItem)
    material_purchases = await fetch(MaterialPurchase)
    product_productions = await fetch(ProductProduction)
    expenses = await fetch(Expense)
    buyers = await fetch(Buyer)
    fair_items = await fetch(FairItem)

    files: dict[str, tuple[list[str], list[dict]]] = {
        "products.csv": (
            ["id", "name", "description", "category", "sale_price", "stock_qty", "created_at"],
            [{"id": r.id, "name": r.name, "description": r.description,
              "category": r.category, "sale_price": r.sale_price,
              "stock_qty": r.stock_qty, "created_at": r.created_at}
             for r in products],
        ),
        "materials.csv": (
            ["id", "name", "unit", "price_per_unit", "stock_qty", "created_at"],
            [{"id": r.id, "name": r.name, "unit": r.unit,
              "price_per_unit": r.price_per_unit, "stock_qty": r.stock_qty,
              "created_at": r.created_at}
             for r in materials],
        ),
        "product_materials.csv": (
            ["id", "product_id", "material_id", "quantity"],
            [{"id": r.id, "product_id": r.product_id,
              "material_id": r.material_id, "quantity": r.quantity}
             for r in product_materials],
        ),
        "sales_channels.csv": (
            ["id", "name", "type", "event_date", "location", "notes", "created_at"],
            [{"id": r.id, "name": r.name, "type": r.type, "event_date": r.event_date,
              "location": r.location, "notes": r.notes, "created_at": r.created_at}
             for r in channels],
        ),
        "sales.csv": (
            ["id", "channel_id", "sale_date", "notes", "created_at"],
            [{"id": r.id, "channel_id": r.channel_id, "sale_date": r.sale_date,
              "notes": r.notes, "created_at": r.created_at}
             for r in sales],
        ),
        "sale_items.csv": (
            ["id", "sale_id", "product_id", "quantity", "price"],
            [{"id": r.id, "sale_id": r.sale_id, "product_id": r.product_id,
              "quantity": r.quantity, "price": r.price}
             for r in sale_items],
        ),
        "material_purchases.csv": (
            ["id", "material_id", "purchased_at", "quantity", "price_per_unit", "total_cost", "created_at"],
            [{"id": r.id, "material_id": r.material_id, "purchased_at": r.purchased_at,
              "quantity": r.quantity, "price_per_unit": r.price_per_unit,
              "total_cost": r.total_cost, "created_at": r.created_at}
             for r in material_purchases],
        ),
           "product_productions.csv": (
              ["id", "product_id", "quantity", "produced_at", "source", "created_at"],
              [{"id": r.id, "product_id": r.product_id, "quantity": r.quantity,
                "produced_at": r.produced_at, "source": r.source,
                "created_at": r.created_at}
               for r in product_productions],
           ),
        "expenses.csv": (
            ["id", "category", "amount", "description", "expense_date", "created_at"],
            [{"id": r.id, "category": r.category, "amount": r.amount,
              "description": r.description, "expense_date": r.expense_date,
              "created_at": r.created_at}
             for r in expenses],
        ),
        "buyers.csv": (
            ["id", "name", "contact", "notes", "created_at"],
            [{"id": r.id, "name": r.name, "contact": r.contact,
              "notes": r.notes, "created_at": r.created_at}
             for r in buyers],
        ),
        "fair_items.csv": (
            ["id", "channel_id", "product_id", "planned_qty"],
            [{"id": r.id, "channel_id": r.channel_id,
              "product_id": r.product_id, "planned_qty": r.planned_qty}
             for r in fair_items],
        ),
        "user_settings.csv": (
            ["id", "currency", "categories", "expense_categories", "material_units", "low_stock_threshold"],
            [{"id": r.id, "currency": r.currency, "categories": r.categories,
              "expense_categories": r.expense_categories, "material_units": r.material_units,
              "low_stock_threshold": r.low_stock_threshold}
             for r in user_settings],
        ),
    }

    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for filename, (fieldnames, rows) in files.items():
            zf.writestr(filename, _make_csv(fieldnames, rows))
    zip_buf.seek(0)

    return StreamingResponse(
        zip_buf,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=craftmanager_export.zip"},
    )
