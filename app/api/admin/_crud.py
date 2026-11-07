"""Route factories shared by the admin resources."""
from flask import jsonify, request

from app.core.errors import ApiError
from app.core.http import json_body, page_args
from app.core.serialize import to_json
from app.dependencies import require_admin


def crud_routes(bp, name, table, parse):
    """list / create / get / update (partial PUT) / delete for one table."""

    @bp.get(f"/{name}", endpoint=f"{name}_list")
    @require_admin
    def list_items():
        return jsonify({"items": to_json(table.list())})

    @bp.post(f"/{name}", endpoint=f"{name}_create")
    @require_admin
    def create_item():
        return jsonify(to_json(table.create(parse(json_body())))), 201

    @bp.get(f"/{name}/<uuid:item_id>", endpoint=f"{name}_get")
    @require_admin
    def get_item(item_id):
        return jsonify(to_json(table.get(item_id)))

    @bp.put(f"/{name}/<uuid:item_id>", endpoint=f"{name}_update")
    @require_admin
    def update_item(item_id):
        values = parse(json_body(), partial=True)
        return jsonify(to_json(table.update(item_id, values)))

    @bp.delete(f"/{name}/<uuid:item_id>", endpoint=f"{name}_delete")
    @require_admin
    def delete_item(item_id):
        table.delete(item_id)
        return "", 204


def inbox_routes(bp, name, service, parse_update, statuses):
    """Paged list (?status=&limit=&offset=), get, status update, delete."""

    @bp.get(f"/{name}", endpoint=f"{name}_list")
    @require_admin
    def list_items():
        status = request.args.get("status")
        if status and status not in statuses:
            raise ApiError(422, "validation_error", "status must be one of: " + ", ".join(statuses))
        limit, offset = page_args()
        items, total = service.list_page(status, limit, offset)
        return jsonify({"items": to_json(items), "total": total})

    @bp.get(f"/{name}/<uuid:item_id>", endpoint=f"{name}_get")
    @require_admin
    def get_item(item_id):
        return jsonify(to_json(service.table.get(item_id)))

    @bp.put(f"/{name}/<uuid:item_id>", endpoint=f"{name}_update")
    @require_admin
    def update_item(item_id):
        return jsonify(to_json(service.table.update(item_id, parse_update(json_body()))))

    @bp.delete(f"/{name}/<uuid:item_id>", endpoint=f"{name}_delete")
    @require_admin
    def delete_item(item_id):
        service.table.delete(item_id)
        return "", 204
