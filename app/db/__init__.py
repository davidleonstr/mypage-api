import atexit

from flask import current_app

from .backend import PsycopgBackend, translate_db_error


def init_db(app, backend=None):
    """Attach a database backend to the app (tests inject their own)."""
    if backend is None:
        backend = PsycopgBackend(app.config["SETTINGS"].database_url)
        atexit.register(backend.close)
    app.extensions["db"] = backend


def fetch_all(sql, params=None):
    try:
        return current_app.extensions["db"].fetch_all(sql, params)
    except Exception as exc:
        translated = translate_db_error(exc)
        if translated is not None:
            raise translated from exc
        raise


def fetch_one(sql, params=None):
    rows = fetch_all(sql, params)
    return rows[0] if rows else None
