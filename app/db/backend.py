from app.core.errors import ApiError


class PsycopgBackend:
    """PostgreSQL access through a psycopg 3 connection pool.

    psycopg is imported lazily so the rest of the app (and the unit tests that
    do not touch the database) can be imported without the driver installed.
    """

    def __init__(self, database_url: str):
        from psycopg.rows import dict_row
        from psycopg_pool import ConnectionPool

        self.pool = ConnectionPool(
            database_url,
            min_size=1,
            max_size=5,
            kwargs={"row_factory": dict_row},
            open=False,
        )
        self.pool.open()

    def fetch_all(self, sql, params=None):
        # The connection context commits on success and rolls back on error.
        with self.pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql, params or {})
                return cur.fetchall() if cur.description else []

    def close(self):
        self.pool.close()


def translate_db_error(exc):
    """Map well-known PostgreSQL errors (by SQLSTATE) to API errors."""
    state = getattr(exc, "sqlstate", None)
    if state == "23505":
        return ApiError(409, "conflict", "A record with the same unique value (e.g. slug) already exists")
    if state == "23503":
        return ApiError(409, "conflict", "The record references, or is referenced by, another record")
    if state in ("23502", "23514", "22001", "22P02", "22003"):
        return ApiError(422, "validation_error", "A value was rejected by the database")
    return None
