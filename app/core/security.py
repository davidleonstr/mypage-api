import hmac


def check_credentials(settings, auth) -> bool:
    """Compare HTTP Basic credentials with the USER / PASSWORD from .env."""
    if auth is None or getattr(auth, "type", None) != "basic":
        return False
    user = (auth.username or "").encode("utf-8")
    password = (auth.password or "").encode("utf-8")
    user_ok = hmac.compare_digest(user, settings.admin_user.encode("utf-8"))
    password_ok = hmac.compare_digest(password, settings.admin_password.encode("utf-8"))
    return user_ok and password_ok
