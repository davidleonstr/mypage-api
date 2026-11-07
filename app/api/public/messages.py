from flask import jsonify

from app.core.http import json_body
from app.dependencies import limit_public_posts
from app.schemas.messages import parse_public_message
from app.services import messages

from . import bp


@bp.post("/messages")
def create_message():
    """Contact form. `website` is a honeypot field that real users leave empty."""
    limit_public_posts()
    data = json_body()
    if data.get("website"):
        return jsonify({"ok": True}), 201  # pretend success, store nothing
    messages.create(parse_public_message(data))
    return jsonify({"ok": True}), 201
