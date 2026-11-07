from flask import request

from app.constants import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE
from app.core.errors import ApiError


def json_body() -> dict:
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ApiError(400, "invalid_json", "Request body must be a JSON object")
    return data


def page_args():
    try:
        limit = int(request.args.get("limit", DEFAULT_PAGE_SIZE))
        offset = int(request.args.get("offset", 0))
    except ValueError:
        raise ApiError(422, "validation_error", "limit and offset must be integers") from None
    if limit < 1 or offset < 0:
        raise ApiError(422, "validation_error", "limit must be >= 1 and offset >= 0")
    return min(limit, MAX_PAGE_SIZE), offset


def register_cors(app, allowed_origins):
    """Allow the listed front-end origins (exact match, no wildcard)."""
    allowed = set(allowed_origins)

    @app.after_request
    def add_headers(response):
        origin = request.headers.get("Origin")
        if origin and origin.rstrip("/") in allowed:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type"
            response.headers["Access-Control-Max-Age"] = "600"
            response.headers.add("Vary", "Origin")
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        if request.path.startswith("/api/admin"):
            response.headers["Cache-Control"] = "no-store"
        return response
