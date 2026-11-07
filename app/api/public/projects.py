from flask import jsonify, request

from app.constants import PROJECT_KINDS
from app.core.errors import ApiError
from app.core.serialize import to_json
from app.schemas.validation import resolve_lang
from app.services import projects

from . import bp


@bp.get("/projects")
def list_projects():
    """Active projects/works, text localised with ?lang=es|en (optional ?kind=)."""
    kind = request.args.get("kind")
    if kind and kind not in PROJECT_KINDS:
        raise ApiError(422, "validation_error", "kind must be one of: " + ", ".join(PROJECT_KINDS))
    lang = resolve_lang(request.args.get("lang"))
    return jsonify({"items": to_json(projects.list_public(lang, kind))})
