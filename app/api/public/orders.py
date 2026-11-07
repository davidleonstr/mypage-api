from flask import jsonify

from app.core.http import json_body
from app.dependencies import limit_public_posts
from app.schemas.orders import parse_public_order
from app.services import orders

from . import bp


@bp.post("/orders")
def create_order():
    """Request a product. Email and phone are required; `website` is a honeypot."""
    limit_public_posts()
    data = json_body()
    if data.get("website"):
        return jsonify({"ok": True}), 201  # pretend success, store nothing
    orders.create_from_request(parse_public_order(data))
    return jsonify({"ok": True}), 201
