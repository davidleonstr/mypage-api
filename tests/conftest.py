"""Test fixtures.

Unit tests run with a database backend that fails if it is ever touched.
Integration tests (test_api.py) run the real SQL against a PostgreSQL database
that already has schema.sql applied. They go through the `psql` command line
client, so they need no Python driver: set TEST_DATABASE (and, if needed, the
usual PGHOST / PGPORT / PGUSER / PGPASSWORD variables) to enable them.
"""
import base64
import json
import os
import re
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import Settings  # noqa: E402
from app.main import create_app  # noqa: E402

PASSWORD = "s3cret-pass"
SETTINGS = Settings(
    database_url="unused",
    admin_user="admin",
    admin_password=PASSWORD,
    cors_origins=("http://localhost:5173",),
)
AUTH = {"Authorization": "Basic " + base64.b64encode(f"admin:{PASSWORD}".encode()).decode()}


class NoDbBackend:
    def fetch_all(self, sql, params=None):
        raise AssertionError("the database must not be used in this test")

    def close(self):
        pass


class DbError(Exception):
    def __init__(self, message, sqlstate):
        super().__init__(message)
        self.sqlstate = sqlstate


_TOKEN = re.compile(r"%\((\w+)\)s|%%")


def _literal(value):
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return "'" + str(value).replace("'", "''") + "'"


class PsqlBackend:
    """Executes the app's queries through psql and returns rows as dicts."""

    def __init__(self, dbname):
        self.dbname = dbname

    def run(self, sql):
        proc = subprocess.run(
            ["psql", "-X", "-A", "-t", "-q", "-v", "ON_ERROR_STOP=1", "-v", "VERBOSITY=verbose",
             "-d", self.dbname, "-c", sql],
            capture_output=True, text=True,
        )
        if proc.returncode != 0:
            match = re.search(r"ERROR:\s+(\w{5}):", proc.stderr)
            raise DbError(proc.stderr.strip(), match.group(1) if match else None)
        return proc.stdout

    def fetch_all(self, sql, params=None):
        params = params or {}
        inlined = _TOKEN.sub(lambda m: "%" if m.group(0) == "%%" else _literal(params[m.group(1)]), sql)
        out = self.run(f"WITH q AS ({inlined}) SELECT coalesce(json_agg(q), '[]'::json) FROM q")
        return json.loads(out)

    def close(self):
        pass


@pytest.fixture
def client():
    return create_app(SETTINGS, NoDbBackend()).test_client()


@pytest.fixture
def db_client():
    dbname = os.environ.get("TEST_DATABASE")
    if not dbname:
        pytest.skip("set TEST_DATABASE to run the PostgreSQL integration tests")
    backend = PsqlBackend(dbname)
    backend.run("TRUNCATE messages, orders, projects, products CASCADE")
    return create_app(SETTINGS, backend).test_client()
