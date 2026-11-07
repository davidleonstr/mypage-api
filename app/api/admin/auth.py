from flask import jsonify

from app.db import fetch_one
from app.dependencies import require_admin

from . import bp


@bp.get("/auth/check")
@require_admin
def check():
    """Lets the admin panel validate the credentials typed into its login form."""
    return jsonify({"ok": True})


@bp.get("/summary")
@require_admin
def summary():
    """Unread counters for the panel badges."""
    return jsonify(fetch_one("SELECT * FROM v_inbox_counts"))
