from app.core.errors import ApiError

from . import products
from .crud import Table

table = Table(
    "orders",
    columns=(
        "product_id", "product_name", "price_cents", "name", "email",
        "phone", "details", "lang", "status",
    ),
    order_by="created_at DESC, id",
)


def create_from_request(values):
    """Store a request, snapshotting the product's name and price."""
    product = products.get_active(values["product_id"])
    if product is None:
        raise ApiError(422, "validation_error", "Some fields are invalid", {"product_id": "unknown product"})
    return table.create(
        {
            **values,
            "product_name": product[f"name_{values['lang']}"],
            "price_cents": product["price_cents"],
        }
    )


def list_page(status, limit, offset):
    where, params = ("status = %(status)s", {"status": status}) if status else ("", {})
    return table.list(where, params, limit, offset), table.count(where, params)
