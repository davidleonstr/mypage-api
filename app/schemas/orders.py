from app.constants import ORDER_STATUSES

from .validation import Validator


def parse_public_order(data):
    v = Validator(data)
    v.uuid("product_id")
    v.text("name", max_len=120)
    v.email("email")
    v.phone("phone")
    v.text("details", max_len=5000, min_len=0, required=False)
    v.lang()
    return v.finish()


def parse_order_update(data):
    v = Validator(data)
    v.choice("status", ORDER_STATUSES)
    return v.finish()
