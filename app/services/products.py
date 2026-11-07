from app.constants import SUPPORTED_LANGS
from app.db import fetch_all, fetch_one

from .crud import Table

table = Table(
    "products",
    columns=(
        "slug", "name_es", "name_en", "description_es", "description_en",
        "price_cents", "note_es", "note_en", "sort_order", "is_active",
    ),
    order_by="sort_order, name_es",
)


def list_public(lang):
    if lang not in SUPPORTED_LANGS:  # lang is interpolated into column names
        raise ValueError(f"Unsupported language: {lang}")
    return fetch_all(
        f"SELECT id, slug, name_{lang} AS name, description_{lang} AS description, "
        f"price_cents, note_{lang} AS note "
        "FROM products WHERE is_active ORDER BY sort_order, name_es"
    )


def get_active(product_id):
    return fetch_one(
        "SELECT id, name_es, name_en, price_cents FROM products WHERE id = %(id)s AND is_active",
        {"id": str(product_id)},
    )
