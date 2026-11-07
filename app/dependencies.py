from functools import wraps

from flask import current_app, request

from app.core.errors import ApiError
from app.core.security import check_credentials


def client_ip() -> str:
    return request.remote_addr or "unknown"


def require_admin(view):
    """Protect a view with HTTP Basic auth (USER / PASSWORD from .env).

    No WWW-Authenticate header is sent on purpose, so browsers do not pop up
    their own login box: the admin panel has its own login form.
    """

    @wraps(view)
    def wrapper(*args, **kwargs):
        failures = current_app.extensions["limiters"]["auth_failures"]
        ip = client_ip()
        if failures.is_limited(ip):
            raise ApiError(429, "too_many_attempts", "Too many failed attempts. Try again later.")
        if not check_credentials(current_app.config["SETTINGS"], request.authorization):
            failures.hit(ip)
            raise ApiError(401, "unauthorized", "Invalid credentials")
        return view(*args, **kwargs)

    return wrapper


def limit_public_posts():
    """Throttle the public forms per client IP."""
    if not current_app.extensions["limiters"]["public_posts"].hit(client_ip()):
        raise ApiError(429, "rate_limited", "Too many submissions. Please try again later.")
