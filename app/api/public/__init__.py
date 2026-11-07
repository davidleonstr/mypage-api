from flask import Blueprint

bp = Blueprint("public", __name__, url_prefix="/api/public")

from . import messages, orders, products, projects  # noqa: E402,F401
