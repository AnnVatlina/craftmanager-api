# Import all models to make them available for Alembic
from app.models.user import User
from app.models.product import Product
from app.models.material import Material
from app.models.product_material import ProductMaterial
from app.models.buyer import Buyer
from app.models.sale import Sale
from app.models.sale_item import SaleItem
from app.models.expense import Expense

__all__ = [
    "User",
    "Product",
    "Material",
    "ProductMaterial",
    "Buyer",
    "Sale",
    "SaleItem",
    "Expense",
]
