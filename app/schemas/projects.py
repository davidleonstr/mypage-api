from app.constants import PROJECT_KINDS

from .validation import Validator


def parse_project(data, *, partial=False):
    v = Validator(data, partial=partial)
    v.slug("slug")
    v.choice("kind", PROJECT_KINDS)
    v.text("name", max_len=120)
    v.text("description_es", max_len=1000, min_len=0, required=False)
    v.text("description_en", max_len=1000, min_len=0, required=False)
    v.url("url")
    v.integer("sort_order", min_value=-100000, max_value=100000)
    v.boolean("is_active")
    return v.finish()
