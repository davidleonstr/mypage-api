from .validation import Validator


def parse_product(data, *, partial=False):
    v = Validator(data, partial=partial)
    v.slug("slug")
    v.text("name_es", max_len=160)
    v.text("name_en", max_len=160)
    v.text("description_es", max_len=1500, min_len=0, required=False)
    v.text("description_en", max_len=1500, min_len=0, required=False)
    # Prices are USD cents: $125 -> 12500.
    v.integer("price_cents", min_value=0, max_value=100_000_000, required=True)
    v.text("note_es", max_len=80, min_len=0, required=False)
    v.text("note_en", max_len=80, min_len=0, required=False)
    v.integer("sort_order", min_value=-100000, max_value=100000)
    v.boolean("is_active")
    return v.finish()
