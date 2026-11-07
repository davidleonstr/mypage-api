from flask import Blueprint

bp = Blueprint("admin", __name__, url_prefix="/api/admin")

from . import auth, messages, orders, products, projects  # noqa: E402,F401
