from app.core.errors import ApiError
from app.db import fetch_all, fetch_one


class Table:
    """Minimal CRUD helper for one table.

    Table and column names are interpolated into the SQL text, so they only
    ever come from the constants declared in the service modules (the column
    whitelist), never from request data. All values travel as bound parameters.
    """

    def __init__(self, name, columns, order_by):
        self.name = name
        self.columns = frozenset(columns)
        self.order_by = order_by

    def _check(self, values):
        unknown = set(values) - self.columns
        if unknown:
            raise ValueError(f"Unknown columns for {self.name}: {sorted(unknown)}")

    def list(self, where="", params=None, limit=None, offset=0):
        sql = f"SELECT * FROM {self.name}"
        if where:
            sql += f" WHERE {where}"
        sql += f" ORDER BY {self.order_by}"
        params = dict(params or {})
        if limit is not None:
            sql += " LIMIT %(limit)s OFFSET %(offset)s"
            params.update(limit=limit, offset=offset)
        return fetch_all(sql, params)

    def count(self, where="", params=None):
        sql = f"SELECT count(*)::int AS total FROM {self.name}"
        if where:
            sql += f" WHERE {where}"
        return fetch_one(sql, params or {})["total"]

    def get(self, item_id):
        row = fetch_one(f"SELECT * FROM {self.name} WHERE id = %(id)s", {"id": str(item_id)})
        if row is None:
            raise ApiError(404, "not_found", "Not found")
        return row

    def create(self, values):
        self._check(values)
        columns = list(values)
        sql = (
            f"INSERT INTO {self.name} ({', '.join(columns)}) "
            f"VALUES ({', '.join('%(v_' + c + ')s' for c in columns)}) RETURNING *"
        )
        return fetch_one(sql, {f"v_{c}": values[c] for c in columns})

    def update(self, item_id, values):
        self._check(values)
        if not values:
            raise ApiError(400, "empty_update", "No fields to update")
        assignments = ", ".join(f"{c} = %(v_{c})s" for c in values)
        params = {f"v_{c}": value for c, value in values.items()}
        params["id"] = str(item_id)
        row = fetch_one(f"UPDATE {self.name} SET {assignments} WHERE id = %(id)s RETURNING *", params)
        if row is None:
            raise ApiError(404, "not_found", "Not found")
        return row

    def delete(self, item_id):
        row = fetch_one(f"DELETE FROM {self.name} WHERE id = %(id)s RETURNING id", {"id": str(item_id)})
        if row is None:
            raise ApiError(404, "not_found", "Not found")
