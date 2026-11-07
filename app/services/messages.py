from .crud import Table

table = Table(
    "messages",
    columns=("name", "email", "subject", "body", "lang", "status"),
    order_by="created_at DESC, id",
)


def create(values):
    return table.create(values)


def list_page(status, limit, offset):
    where, params = ("status = %(status)s", {"status": status}) if status else ("", {})
    return table.list(where, params, limit, offset), table.count(where, params)
