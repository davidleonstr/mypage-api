from . import admin, health, public


def register_blueprints(app):
    app.register_blueprint(health.bp)
    app.register_blueprint(public.bp)
    app.register_blueprint(admin.bp)
