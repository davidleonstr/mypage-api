from app.constants import INBOX_STATUSES

from .validation import Validator


def parse_public_message(data):
    v = Validator(data)
    v.text("name", max_len=120)
    v.email("email")
    v.text("subject", max_len=200, min_len=0, required=False)
    v.text("body", max_len=5000)
    v.lang()
    return v.finish()


def parse_message_update(data):
    v = Validator(data)
    v.choice("status", INBOX_STATUSES)
    return v.finish()
