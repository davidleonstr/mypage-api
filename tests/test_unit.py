import pytest

from app.config import Settings, load_settings
from app.core.ratelimit import RateLimiter
from app.main import create_app
from app.schemas.validation import Validator, resolve_lang
from app.core.errors import ApiError

from conftest import AUTH, NoDbBackend, SETTINGS


# ---- configuration -------------------------------------------------------

def test_credentials_come_from_api_env_not_the_os_user_variable(tmp_path, monkeypatch):
    env = tmp_path / ".env"
    env.write_text("USER = david\nPASSWORD = hunter2-hunter2\n")
    monkeypatch.setenv("USER", "some-os-user")
    monkeypatch.delenv("ADMIN_USER", raising=False)
    settings = load_settings(env)
    assert settings.admin_user == "david"
    assert settings.admin_password == "hunter2-hunter2"

    env.write_text("PASSWORD=abc12345\n")
    assert load_settings(env).admin_user == ""  # the OS USER must not leak in


@pytest.mark.parametrize("password", ["", "change-me"])
def test_app_refuses_to_start_without_a_real_password(password):
    settings = Settings(database_url="x", admin_user="admin", admin_password=password)
    with pytest.raises(RuntimeError):
        create_app(settings, NoDbBackend())


# ---- validation ----------------------------------------------------------

def test_resolve_lang():
    assert resolve_lang("en-US") == "en"
    assert resolve_lang("ES") == "es"
    assert resolve_lang("ar") == "es"
    assert resolve_lang(None) == "es"


def test_validator_collects_errors_and_whitelists_fields():
    v = Validator({"email": "nope", "phone": "12", "price": True, "extra": "x"})
    v.email("email")
    v.phone("phone")
    v.integer("price")
    with pytest.raises(ApiError) as exc:
        v.finish()
    assert set(exc.value.fields) == {"email", "phone", "price"}


def test_partial_validation_skips_missing_fields():
    v = Validator({"name": "  Hola  "}, partial=True)
    v.text("name", max_len=10)
    v.url("url")
    assert v.finish() == {"name": "Hola"}


def test_url_and_slug_rules():
    v = Validator({"url": "javascript:alert(1)", "slug": "Bad Slug"})
    v.url("url")
    v.slug("slug")
    with pytest.raises(ApiError) as exc:
        v.finish()
    assert set(exc.value.fields) == {"url", "slug"}


# ---- rate limiter --------------------------------------------------------

def test_rate_limiter():
    limiter = RateLimiter(2, 60)
    assert limiter.hit("ip") and limiter.hit("ip")
    assert not limiter.hit("ip")
    assert limiter.is_limited("ip")
    assert not limiter.is_limited("other")


# ---- auth ----------------------------------------------------------------

def test_admin_requires_credentials(client):
    res = client.get("/api/admin/auth/check")
    assert res.status_code == 401
    assert "WWW-Authenticate" not in res.headers  # no browser login popup
    assert res.get_json()["error"]["code"] == "unauthorized"

    bad = {"Authorization": "Basic YWRtaW46d3Jvbmc="}  # admin:wrong
    assert client.get("/api/admin/auth/check", headers=bad).status_code == 401
    assert client.get("/api/admin/auth/check", headers=AUTH).status_code == 200


def test_every_admin_route_is_protected(client):
    # Many unauthenticated calls below: lift the failed-login lockout for this test.
    client.application.extensions["limiters"]["auth_failures"] = RateLimiter(10**6, 60)
    for rule in client.application.url_map.iter_rules():
        if not rule.rule.startswith("/api/admin"):
            continue
        url = rule.rule.replace("<uuid:item_id>", "00000000-0000-0000-0000-000000000000")
        for method in rule.methods - {"HEAD", "OPTIONS"}:
            assert client.open(url, method=method).status_code == 401, (method, rule.rule)


def test_too_many_failed_logins_are_blocked(client):
    for _ in range(10):
        assert client.get("/api/admin/auth/check").status_code == 401
    assert client.get("/api/admin/auth/check", headers=AUTH).status_code == 429


# ---- public forms (no database needed for these paths) --------------------

def test_message_validation(client):
    res = client.post("/api/public/messages", json={"name": "", "email": "bad", "body": ""})
    assert res.status_code == 422
    assert set(res.get_json()["error"]["fields"]) == {"name", "email", "body"}


def test_order_requires_email_and_phone(client):
    res = client.post("/api/public/orders", json={"product_id": "x", "name": "Ana"})
    assert res.status_code == 422
    assert {"product_id", "email", "phone"} <= set(res.get_json()["error"]["fields"])


def test_honeypot_is_accepted_but_never_stored(client):
    res = client.post("/api/public/messages", json={"website": "http://spam", "name": "x"})
    assert res.status_code == 201  # NoDbBackend would raise if anything were stored


def test_public_posts_are_rate_limited(client):
    for _ in range(10):
        assert client.post("/api/public/messages", json={"website": "bot"}).status_code == 201
    assert client.post("/api/public/messages", json={"website": "bot"}).status_code == 429


def test_invalid_json_body(client):
    res = client.post("/api/public/messages", data="not json", content_type="application/json")
    assert res.status_code == 400


# ---- cors ----------------------------------------------------------------

def test_cors_allows_only_configured_origins(client):
    ok = client.get("/api/admin/auth/check", headers={"Origin": "http://localhost:5173"})
    assert ok.headers["Access-Control-Allow-Origin"] == "http://localhost:5173"
    other = client.get("/api/admin/auth/check", headers={"Origin": "https://evil.example"})
    assert "Access-Control-Allow-Origin" not in other.headers
