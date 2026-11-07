from flask import jsonify, request

from app.core.serialize import to_json
from app.schemas.validation import resolve_lang
from app.services import products

from . import bp


@bp.get("/products")
def list_products():
    """Active products, text localised with ?lang=es|en. Prices are USD cents."""
    lang = resolve_lang(request.args.get("lang"))
    return jsonify({"items": to_json(products.list_public(lang))})
