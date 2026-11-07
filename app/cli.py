import click
from flask import current_app

from app.db import fetch_one


def register_cli(app):
    @app.cli.command("check")
    def check():
        """Verify the configuration and the database connection."""
        settings = current_app.config["SETTINGS"]
        click.echo(f"Admin user: {settings.admin_user}")
        click.echo(f"CORS origins: {', '.join(settings.cors_origins) or '(none)'}")
        try:
            counts = fetch_one("SELECT * FROM v_inbox_counts")
        except Exception as exc:  # noqa: BLE001 - report any connection/schema problem
            raise click.ClickException(f"Database check failed: {exc}") from exc
        click.echo(f"Database OK ({counts['new_messages']} new messages, {counts['new_orders']} new orders)")
