import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATABASE_URL = "postgresql://postgres:postgres@localhost:5432/portfolio"
PLACEHOLDER_PASSWORDS = {"", "change-me", "changeme"}


@dataclass(frozen=True)
class Settings:
    database_url: str
    admin_user: str
    admin_password: str
    cors_origins: tuple = ()
    trust_proxy: bool = False

    def validate(self) -> None:
        problems = []
        if not self.admin_user:
            problems.append("USER is not set in .env")
        if self.admin_password.strip().lower() in PLACEHOLDER_PASSWORDS:
            problems.append("PASSWORD is not set (or is still the placeholder) in .env")
        if problems:
            raise RuntimeError("Invalid configuration: " + "; ".join(problems))


def load_settings(env_file=None) -> Settings:
    """Read .env.

    The admin credentials are the USER / PASSWORD keys of .env. They are read
    from the file only (ADMIN_USER / ADMIN_PASSWORD in the process environment
    are accepted as a fallback), because the OS already defines a USER variable
    in most shells and it must never be mistaken for the admin name.
    """
    path = Path(env_file or os.environ.get("API_ENV_FILE") or ROOT / ".env")
    values = dotenv_values(path) if path.exists() else {}

    def pick(key, env_key=None, default=""):
        value = (values.get(key) or "").strip()
        if value:
            return value
        return (os.environ.get(env_key or key) or "").strip() or default

    origins = pick("CORS_ORIGINS", default="http://localhost:5173")
    return Settings(
        database_url=pick("DATABASE_URL", default=DEFAULT_DATABASE_URL),
        admin_user=pick("USER", "ADMIN_USER"),
        admin_password=pick("PASSWORD", "ADMIN_PASSWORD"),
        cors_origins=tuple(o.strip().rstrip("/") for o in origins.split(",") if o.strip()),
        trust_proxy=pick("TRUST_PROXY", default="0").lower() in ("1", "true", "yes"),
    )
