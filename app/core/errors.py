import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

log = logging.getLogger(__name__)


class ApiError(Exception):
    """Raised anywhere in the API to produce a JSON error response."""

    def __init__(self, status, code, message, fields=None):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message
        self.fields = fields


def error_body(code, message, fields=None):
    body = {"error": {"code": code, "message": message}}
    if fields:
        body["error"]["fields"] = fields
    return body


def register_error_handlers(app):
    @app.errorhandler(ApiError)
    def handle_api_error(err):
        return jsonify(error_body(err.code, err.message, err.fields)), err.status

    @app.errorhandler(HTTPException)
    def handle_http_error(err):
        code = (err.name or "error").lower().replace(" ", "_")
        return jsonify(error_body(code, err.description or err.name)), err.code

    @app.errorhandler(Exception)
    def handle_unexpected(err):
        log.exception("Unhandled error")
        return jsonify(error_body("internal_error", "Internal server error")), 500
