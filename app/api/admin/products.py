from app.schemas.products import parse_product
from app.services import products

from . import bp
from ._crud import crud_routes

crud_routes(bp, "products", products.table, parse_product)
