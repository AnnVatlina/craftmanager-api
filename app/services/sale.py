from decimal import Decimal
from app.models import Sale


def calc_sale_total_amount(sale: Sale) -> Decimal:
    """Calculate the total amount of a sale from its items"""
    total = Decimal("0")
    for item in sale.items:
        total += item.quantity * item.price
    return total
