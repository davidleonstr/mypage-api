import re
import uuid as uuidlib
from urllib.parse import urlsplit

from app.constants import DEFAULT_LANG, SUPPORTED_LANGS
from app.core.errors import ApiError

_MISSING = object()
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
PHONE_RE = re.compile(r"^[0-9+()\-.\s]+$")


def resolve_lang(value) -> str:
    """Normalise 'es', 'en-US', ... to a supported language, else the default."""
    if isinstance(value, str):
        base = value.split("-")[0].strip().lower()
        if base in SUPPORTED_LANGS:
            return base
    return DEFAULT_LANG


class Validator:
    """Collects field errors and returns only the cleaned, whitelisted values.

    With partial=True (used by PUT) missing fields are simply skipped, so the
    client can send only what it wants to change.
    """

    def __init__(self, data: dict, *, partial: bool = False):
        self.data = data
        self.partial = partial
        self.out = {}
        self.errors = {}

    def _get(self, key, required):
        value = self.data.get(key)
        if value is None:
            if required and not self.partial:
                self.errors[key] = "is required"
            return _MISSING
        return value

    def text(self, key, *, max_len, min_len=1, required=True):
        value = self._get(key, required)
        if value is _MISSING:
            return
        if not isinstance(value, str):
            self.errors[key] = "must be a string"
            return
        value = value.strip()
        if len(value) < min_len:
            self.errors[key] = "is required" if min_len == 1 else f"must be at least {min_len} characters"
        elif len(value) > max_len:
            self.errors[key] = f"must be at most {max_len} characters"
        else:
            self.out[key] = value

    def email(self, key, *, required=True):
        value = self._get(key, required)
        if value is _MISSING:
            return
        if not isinstance(value, str):
            self.errors[key] = "must be a string"
            return
        value = value.strip()
        if len(value) > 254 or not EMAIL_RE.match(value):
            self.errors[key] = "must be a valid email address"
        else:
            self.out[key] = value

    def phone(self, key, *, required=True):
        value = self._get(key, required)
        if value is _MISSING:
            return
        if not isinstance(value, str):
            self.errors[key] = "must be a string"
            return
        value = value.strip()
        digits = sum(ch.isdigit() for ch in value)
        if not (5 <= len(value) <= 40) or not PHONE_RE.match(value) or digits < 5:
            self.errors[key] = "must be a valid phone number"
        else:
            self.out[key] = value

    def integer(self, key, *, min_value=None, max_value=None, required=False):
        value = self._get(key, required)
        if value is _MISSING:
            return
        if isinstance(value, bool) or not isinstance(value, int):
            self.errors[key] = "must be an integer"
        elif min_value is not None and value < min_value:
            self.errors[key] = f"must be >= {min_value}"
        elif max_value is not None and value > max_value:
            self.errors[key] = f"must be <= {max_value}"
        else:
            self.out[key] = value

    def boolean(self, key, *, required=False):
        value = self._get(key, required)
        if value is _MISSING:
            return
        if not isinstance(value, bool):
            self.errors[key] = "must be true or false"
        else:
            self.out[key] = value

    def choice(self, key, options, *, required=True):
        value = self._get(key, required)
        if value is _MISSING:
            return
        if value not in options:
            self.errors[key] = "must be one of: " + ", ".join(options)
        else:
            self.out[key] = value

    def url(self, key, *, required=True, max_len=2000):
        value = self._get(key, required)
        if value is _MISSING:
            return
        if not isinstance(value, str):
            self.errors[key] = "must be a string"
            return
        value = value.strip()
        parts = urlsplit(value)
        if len(value) > max_len or parts.scheme not in ("http", "https") or not parts.netloc:
            self.errors[key] = "must be an http(s) URL"
        else:
            self.out[key] = value

    def slug(self, key, *, required=True, max_len=80):
        value = self._get(key, required)
        if value is _MISSING:
            return
        if not isinstance(value, str) or len(value) > max_len or not SLUG_RE.match(value):
            self.errors[key] = "must be lowercase letters, numbers and hyphens (e.g. my-project)"
        else:
            self.out[key] = value

    def uuid(self, key, *, required=True):
        value = self._get(key, required)
        if value is _MISSING:
            return
        try:
            self.out[key] = str(uuidlib.UUID(str(value)))
        except ValueError:
            self.errors[key] = "must be a valid id"

    def lang(self, key="lang"):
        self.out[key] = resolve_lang(self.data.get(key))

    def finish(self) -> dict:
        if self.errors:
            raise ApiError(422, "validation_error", "Some fields are invalid", self.errors)
        return self.out
