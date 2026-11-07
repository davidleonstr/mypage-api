from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

from app.api import register_blueprints
from app.cli import register_cli
from app.config import load_settings
from app.constants import FAILED_LOGINS_PER_15_MIN, PUBLIC_POSTS_PER_HOUR
from app.core.errors import register_error_handlers
from app.core.http import register_cors
from app.core.ratelimit import RateLimiter
from app.db import init_db


def create_app(settings=None, db_backend=None):
    settings = settings or load_settings()
    settings.validate()  # refuses to start without USER / PASSWORD in .env

    app = Flask(__name__)
    app.config["SETTINGS"] = settings
    app.config["MAX_CONTENT_LENGTH"] = 64 * 1024
    app.json.ensure_ascii = False
    app.json.sort_keys = False

    if settings.trust_proxy:
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    app.extensions["limiters"] = {
        "public_posts": RateLimiter(PUBLIC_POSTS_PER_HOUR, 3600),
        "auth_failures": RateLimiter(FAILED_LOGINS_PER_15_MIN, 900),
    }

    init_db(app, db_backend)
    register_cors(app, settings.cors_origins)
    register_error_handlers(app)
    register_blueprints(app)
    register_cli(app)
    return app
