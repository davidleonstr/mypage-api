import logging

from flask import Blueprint, jsonify

from app.db import fetch_one

log = logging.getLogger(__name__)
bp = Blueprint("health", __name__, url_prefix="/api")


@bp.get("/health")
def health():
    try:
        fetch_one("SELECT 1 AS ok")
    except Exception:
        log.exception("Health check: database unreachable")
        return jsonify({"status": "degraded", "db": "down"}), 503
    return jsonify({"status": "ok", "db": "up"})
