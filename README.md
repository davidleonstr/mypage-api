# Portfolio API

Flask + PostgreSQL API for the portfolio site: projects, shop products, a contact form, product requests, and an admin panel backend.

## Run it

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

copy .env.example .env      # then edit USER / PASSWORD / DATABASE_URL
psql -d portfolio -f ..\portfolio-db\schema.sql   # run from the db folder, see its README

flask --app wsgi check            # config + database sanity check
flask --app wsgi run --debug      # http://127.0.0.1:5000
```

Production (Linux): `pm2 start ecosystem.config.js` (gunicorn, port 5000) behind nginx/Caddy, with `TRUST_PROXY=1` in `.env`.

## Login

There is one administrator, defined in `.env`:

```
USER=admin
PASSWORD=a-long-random-password
```

Admin endpoints use HTTP Basic auth with those values. The API will not start if `PASSWORD` is empty or still `change-me`. There is no user table and no token: the admin panel keeps the credentials in `sessionStorage` for the tab and sends them with each request. After 10 failed attempts an IP is blocked for 15 minutes. Serve the API over HTTPS in production, since Basic auth sends the password on every call.

## Endpoints

Errors are always `{"error": {"code", "message", "fields?"}}`. Prices are USD cents. Text fields exist in `es` and `en`.

### Public (no auth)

| Method | Path | Notes |
| --- | --- | --- |
| GET | `/api/health` | `200` or `503` if the database is down |
| GET | `/api/public/projects?lang=es&kind=project\|work` | active projects, text localised |
| GET | `/api/public/products?lang=es` | active products, text localised |
| POST | `/api/public/messages` | contact form: `name`, `email`, `body`, optional `subject`, `lang` |
| POST | `/api/public/orders` | product request: `product_id`, `name`, `email`, `phone` (all required), optional `details`, `lang` |

Both POST endpoints accept a hidden `website` field as a honeypot (bots fill it, the request is silently dropped) and are limited to 10 submissions per hour per IP.

### Admin (Basic auth)

| Method | Path | Notes |
| --- | --- | --- |
| GET | `/api/admin/auth/check` | validates the credentials |
| GET | `/api/admin/summary` | `{new_messages, new_orders}` |
| GET, POST | `/api/admin/projects` | list all (including inactive) / create |
| GET, PUT, DELETE | `/api/admin/projects/<id>` | `PUT` is partial: send only the fields to change |
| GET, POST | `/api/admin/products` | same shape as projects |
| GET, PUT, DELETE | `/api/admin/products/<id>` | |
| GET | `/api/admin/messages?status=&limit=&offset=` | `{items, total}` |
| GET, PUT, DELETE | `/api/admin/messages/<id>` | `PUT {"status": "new\|read\|archived"}` |
| GET | `/api/admin/orders?status=&limit=&offset=` | `{items, total}` |
| GET, PUT, DELETE | `/api/admin/orders/<id>` | `PUT {"status": "new\|contacted\|done\|cancelled"}` |

Orders store a snapshot of the product name and price at the time of the request, so they stay readable if the product is edited or deleted.

## Tests

```powershell
pip install -r requirements-dev.txt
pytest                                  # unit tests only
$env:TEST_DATABASE = "portfolio_test"   # a database with schema.sql applied
pytest                                  # also runs the PostgreSQL integration tests
```

The integration tests run the real queries through the `psql` command line client (so `psql` must be on the PATH) and empty the `projects`, `products`, `messages` and `orders` tables of that database before each test. Never point `TEST_DATABASE` at your real database.

## Layout

```
app/
  main.py            create_app()
  config.py          reads .env
  dependencies.py    require_admin, public rate limit
  api/               health, public/ and admin/ blueprints
  schemas/           request validation
  services/          SQL and business rules
  db/                psycopg connection pool
  core/              errors, CORS, rate limiter, serialisation
tests/
wsgi.py
```
