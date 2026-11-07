from app.constants import ORDER_STATUSES
from app.schemas.orders import parse_order_update
from app.services import orders

from . import bp
from ._crud import inbox_routes

inbox_routes(bp, "orders", orders, parse_order_update, ORDER_STATUSES)
