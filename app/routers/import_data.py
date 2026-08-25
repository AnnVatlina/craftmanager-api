import csv
import io
import uuid
import zipfile
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.buyer import Buyer
from app.models.expense import Expense
from app.models.fair_item import FairItem
from app.models.material import Material
from app.models.material_purchase import MaterialPurchase
from app.models.product import Product
from app.models.product_material import ProductMaterial
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.models.sales_channel import SalesChannel
from app.models.user import User
from app.models.user_setting import UserSetting

router = APIRouter(
    prefix="/import",
    tags=["import"],
    dependencies=[Depends(get_current_user)],
)


def _uuid(val: str):
    try:
        return uuid.UUID(val)
    except (ValueError, AttributeError):
        return None


def _date(val: str):
    if not val:
        return None
    try:
        return date.fromisoformat(val)
    except ValueError:
        return None


def _dt(val: str):
    if not val:
        return None
    try:
        return datetime.fromisoformat(val)
    except ValueError:
        return None


def _dec(val: str):
    if not val:
        return None
    try:
        return Decimal(val)
    except InvalidOperation:
        return None


def _int(val: str):
    if not val:
        return None
    try:
        return int(val)
    except ValueError:
        return None


def _opt(val: str):
    return val if val else None


def _read_csv(zf: zipfile.ZipFile, name: str) -> list[dict]:
    if name not in zf.namelist():
        return []
    with zf.open(name) as f:
        text = f.read().decode("utf-8")
    return list(csv.DictReader(io.StringIO(text)))


@router.post("/csv")
async def import_all_csv(
    file: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not (file.filename or "").endswith(".zip"):
        raise HTTPException(status_code=400, detail="Ожидается ZIP-файл")

    content = await file.read()
    try:
        zf = zipfile.ZipFile(io.BytesIO(content))
    except zipfile.BadZipFile:
        raise HTTPException(status_code=400, detail="Неверный ZIP-файл")

    uid = user.id
    counts: dict[str, int] = {}

    # 1. buyers — нет FK-зависимостей
    rows = _read_csv(zf, "buyers.csv")
    values = [
        {"id": _uuid(r["id"]), "user_id": uid, "name": r["name"],
         "contact": _opt(r.get("contact")), "notes": _opt(r.get("notes")),
         "created_at": _dt(r.get("created_at")) or datetime.utcnow()}
        for r in rows if _uuid(r.get("id")) and r.get("name")
    ]
    if values:
        await db.execute(insert(Buyer).values(values).on_conflict_do_nothing())
    counts["buyers"] = len(values)

    # 2. sales_channels — нет FK-зависимостей
    rows = _read_csv(zf, "sales_channels.csv")
    values = [
        {"id": _uuid(r["id"]), "user_id": uid, "name": r["name"],
         "type": r.get("type") or "лс",
         "event_date": _date(r.get("event_date")),
         "location": _opt(r.get("location")), "notes": _opt(r.get("notes")),
         "created_at": _dt(r.get("created_at")) or datetime.utcnow()}
        for r in rows if _uuid(r.get("id")) and r.get("name")
    ]
    if values:
        await db.execute(insert(SalesChannel).values(values).on_conflict_do_nothing())
    counts["sales_channels"] = len(values)

    # 3. materials — нет FK-зависимостей
    rows = _read_csv(zf, "materials.csv")
    values = [
        {"id": _uuid(r["id"]), "user_id": uid, "name": r["name"],
         "unit": r.get("unit") or "шт",
         "price_per_unit": _dec(r.get("price_per_unit")) or Decimal("0"),
         "stock_qty": _dec(r.get("stock_qty")) or Decimal("0"),
         "created_at": _dt(r.get("created_at")) or datetime.utcnow()}
        for r in rows if _uuid(r.get("id")) and r.get("name")
    ]
    if values:
        await db.execute(insert(Material).values(values).on_conflict_do_nothing())
    counts["materials"] = len(values)

    # 4. products — нет FK-зависимостей
    rows = _read_csv(zf, "products.csv")
    values = [
        {"id": _uuid(r["id"]), "user_id": uid, "name": r["name"],
         "description": _opt(r.get("description")),
         "category": _opt(r.get("category")),
         "sale_price": _dec(r.get("sale_price")) or Decimal("0"),
         "stock_qty": _int(r.get("stock_qty")) or 0,
         "created_at": _dt(r.get("created_at")) or datetime.utcnow()}
        for r in rows if _uuid(r.get("id")) and r.get("name")
    ]
    if values:
        await db.execute(insert(Product).values(values).on_conflict_do_nothing())
    counts["products"] = len(values)

    # 5. expenses — нет FK-зависимостей
    rows = _read_csv(zf, "expenses.csv")
    values = [
        {"id": _uuid(r["id"]), "user_id": uid,
         "category": r.get("category") or "прочее",
         "amount": _dec(r.get("amount")) or Decimal("0"),
         "description": _opt(r.get("description")),
         "expense_date": _date(r.get("expense_date")) or date.today(),
         "created_at": _dt(r.get("created_at")) or datetime.utcnow()}
        for r in rows if _uuid(r.get("id"))
    ]
    if values:
        await db.execute(insert(Expense).values(values).on_conflict_do_nothing())
    counts["expenses"] = len(values)

    # 6. product_materials — зависит от products, materials
    rows = _read_csv(zf, "product_materials.csv")
    values = [
        {"id": _uuid(r["id"]), "user_id": uid,
         "product_id": _uuid(r.get("product_id")),
         "material_id": _uuid(r.get("material_id")),
         "quantity": _dec(r.get("quantity")) or Decimal("0")}
        for r in rows
        if _uuid(r.get("id")) and _uuid(r.get("product_id")) and _uuid(r.get("material_id"))
    ]
    if values:
        await db.execute(insert(ProductMaterial).values(values).on_conflict_do_nothing())
    counts["product_materials"] = len(values)

    # 7. sales — зависит от sales_channels
    rows = _read_csv(zf, "sales.csv")
    values = [
        {"id": _uuid(r["id"]), "user_id": uid,
         "channel_id": _uuid(r.get("channel_id")),
         "sale_date": _date(r.get("sale_date")) or date.today(),
         "notes": _opt(r.get("notes")),
         "created_at": _dt(r.get("created_at")) or datetime.utcnow()}
        for r in rows if _uuid(r.get("id"))
    ]
    if values:
        await db.execute(insert(Sale).values(values).on_conflict_do_nothing())
    counts["sales"] = len(values)

    # 8. sale_items — зависит от sales, products
    rows = _read_csv(zf, "sale_items.csv")
    values = [
        {"id": _uuid(r["id"]), "user_id": uid,
         "sale_id": _uuid(r.get("sale_id")),
         "product_id": _uuid(r.get("product_id")),
         "quantity": _int(r.get("quantity")) or 1,
         "price": _dec(r.get("price")) or Decimal("0")}
        for r in rows if _uuid(r.get("id")) and _uuid(r.get("sale_id"))
    ]
    if values:
        await db.execute(insert(SaleItem).values(values).on_conflict_do_nothing())
    counts["sale_items"] = len(values)

    # 9. material_purchases — зависит от materials
    rows = _read_csv(zf, "material_purchases.csv")
    values = [
        {"id": _uuid(r["id"]), "user_id": uid,
         "material_id": _uuid(r.get("material_id")),
         "purchased_at": _date(r.get("purchased_at")) or date.today(),
         "quantity": _dec(r.get("quantity")) or Decimal("0"),
         "price_per_unit": _dec(r.get("price_per_unit")) or Decimal("0"),
         "total_cost": _dec(r.get("total_cost")) or Decimal("0"),
         "created_at": _dt(r.get("created_at")) or datetime.utcnow()}
        for r in rows if _uuid(r.get("id")) and _uuid(r.get("material_id"))
    ]
    if values:
        await db.execute(insert(MaterialPurchase).values(values).on_conflict_do_nothing())
    counts["material_purchases"] = len(values)

    # 10. fair_items — зависит от sales_channels, products
    rows = _read_csv(zf, "fair_items.csv")
    values = [
        {"id": _uuid(r["id"]), "user_id": uid,
         "channel_id": _uuid(r.get("channel_id")),
         "product_id": _uuid(r.get("product_id")),
         "planned_qty": _int(r.get("planned_qty")) or 0}
        for r in rows
        if _uuid(r.get("id")) and _uuid(r.get("channel_id")) and _uuid(r.get("product_id"))
    ]
    if values:
        await db.execute(insert(FairItem).values(values).on_conflict_do_nothing())
    counts["fair_items"] = len(values)

    # 11. user_settings — upsert по user_id (настройки всегда перезаписываются)
    rows = _read_csv(zf, "user_settings.csv")
    if rows:
        r = rows[0]
        set_vals = {
            "currency": r.get("currency") or "Br",
            "categories": r.get("categories") or "",
            "expense_categories": r.get("expense_categories") or "",
            "material_units": r.get("material_units") or "",
            "low_stock_threshold": _int(r.get("low_stock_threshold")) or 5,
        }
        stmt = (
            insert(UserSetting)
            .values(id=_uuid(r.get("id")) or uuid.uuid4(), user_id=uid, **set_vals)
            .on_conflict_do_update(index_elements=["user_id"], set_=set_vals)
        )
        await db.execute(stmt)
    counts["user_settings"] = len(rows)

    await db.commit()

    return {"data": {"imported": counts}}
