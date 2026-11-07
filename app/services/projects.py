from app.constants import SUPPORTED_LANGS
from app.db import fetch_all

from .crud import Table

table = Table(
    "projects",
    columns=("slug", "kind", "name", "description_es", "description_en", "url", "sort_order", "is_active"),
    order_by="kind, sort_order, name",
)


def list_public(lang, kind=None):
    if lang not in SUPPORTED_LANGS:  # lang is interpolated into a column name
        raise ValueError(f"Unsupported language: {lang}")
    sql = (
        f"SELECT id, slug, kind, name, description_{lang} AS description, url "
        "FROM projects WHERE is_active"
    )
    params = {}
    if kind:
        sql += " AND kind = %(kind)s"
        params["kind"] = kind
    sql += " ORDER BY kind, sort_order, name"
    return fetch_all(sql, params)
