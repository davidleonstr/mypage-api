"""Integration tests: real SQL against PostgreSQL (see conftest.py)."""
from conftest import AUTH


def make_product(client, **overrides):
    body = {
        "slug": "landing", "name_es": "Landing", "name_en": "Landing page",
        "description_es": "Una página", "description_en": "One page",
        "price_cents": 12500, "note_es": "Precio inicial", "note_en": "Starting price",
        "sort_order": 1,
    }
    body.update(overrides)
    res = client.post("/api/admin/products", json=body, headers=AUTH)
    assert res.status_code == 201, res.get_json()
    return res.get_json()


def make_project(client, **overrides):
    body = {
        "slug": "my-wall", "kind": "project", "name": "My wall",
        "description_es": "Un muro", "description_en": "A wall",
        "url": "https://mywall.example/", "sort_order": 1,
    }
    body.update(overrides)
    res = client.post("/api/admin/projects", json=body, headers=AUTH)
    assert res.status_code == 201, res.get_json()
    return res.get_json()


ORDER = {"name": "Ana", "email": "Ana@Example.com", "phone": "+503 7000 0000", "details": "Need it by May"}


def test_health(db_client):
    assert db_client.get("/api/health").get_json() == {"status": "ok", "db": "up"}


def test_project_crud_and_public_listing(db_client):
    created = make_project(db_client)
    assert created["is_active"] is True and "id" in created

    dup = db_client.post("/api/admin/projects", headers=AUTH, json={
        "slug": "my-wall", "kind": "work", "name": "Dup", "url": "https://x.example"})
    assert dup.status_code == 409

    updated = db_client.put(f"/api/admin/projects/{created['id']}", headers=AUTH,
                            json={"name": "My wall 2", "sort_order": 5})
    assert updated.get_json()["name"] == "My wall 2"
    assert updated.get_json()["description_en"] == "A wall"  # untouched

    es = db_client.get("/api/public/projects?lang=es").get_json()["items"]
    en = db_client.get("/api/public/projects?lang=en-US").get_json()["items"]
    assert es[0]["description"] == "Un muro" and en[0]["description"] == "A wall"
    assert db_client.get("/api/public/projects?kind=work").get_json()["items"] == []

    db_client.put(f"/api/admin/projects/{created['id']}", headers=AUTH, json={"is_active": False})
    assert db_client.get("/api/public/projects").get_json()["items"] == []
    assert len(db_client.get("/api/admin/projects", headers=AUTH).get_json()["items"]) == 1

    assert db_client.delete(f"/api/admin/projects/{created['id']}", headers=AUTH).status_code == 204
    assert db_client.get(f"/api/admin/projects/{created['id']}", headers=AUTH).status_code == 404


def test_project_validation_errors(db_client):
    res = db_client.post("/api/admin/projects", headers=AUTH,
                         json={"slug": "Bad Slug", "kind": "other", "name": "", "url": "ftp://x"})
    assert res.status_code == 422
    assert set(res.get_json()["error"]["fields"]) == {"slug", "kind", "name", "url"}
    assert db_client.put("/api/admin/projects/not-a-uuid", headers=AUTH, json={}).status_code == 404


def test_product_crud_and_localised_listing(db_client):
    product = make_product(db_client)
    bad = db_client.post("/api/admin/products", headers=AUTH, json={
        "slug": "x", "name_es": "x", "name_en": "x", "price_cents": -5})
    assert bad.status_code == 422

    item = db_client.get("/api/public/products?lang=en").get_json()["items"][0]
    assert item["name"] == "Landing page" and item["note"] == "Starting price"
    assert item["price_cents"] == 12500 and item["id"] == product["id"]
    assert db_client.get("/api/public/products?lang=ar").get_json()["items"][0]["name"] == "Landing"  # -> es


def test_order_flow(db_client):
    product = make_product(db_client)
    res = db_client.post("/api/public/orders", json={**ORDER, "product_id": product["id"], "lang": "en"})
    assert res.status_code == 201

    listing = db_client.get("/api/admin/orders", headers=AUTH).get_json()
    assert listing["total"] == 1
    order = listing["items"][0]
    assert order["product_name"] == "Landing page" and order["price_cents"] == 12500
    assert order["status"] == "new" and order["lang"] == "en"

    assert db_client.get("/api/admin/summary", headers=AUTH).get_json() == {"new_messages": 0, "new_orders": 1}

    res = db_client.put(f"/api/admin/orders/{order['id']}", headers=AUTH, json={"status": "contacted"})
    assert res.get_json()["status"] == "contacted"
    assert db_client.get("/api/admin/orders?status=new", headers=AUTH).get_json()["total"] == 0
    assert db_client.get("/api/admin/orders?status=bogus", headers=AUTH).status_code == 422
    assert db_client.put(f"/api/admin/orders/{order['id']}", headers=AUTH,
                         json={"status": "bogus"}).status_code == 422


def test_order_keeps_snapshot_when_product_is_deleted(db_client):
    product = make_product(db_client)
    db_client.post("/api/public/orders", json={**ORDER, "product_id": product["id"], "lang": "es"})
    assert db_client.delete(f"/api/admin/products/{product['id']}", headers=AUTH).status_code == 204
    order = db_client.get("/api/admin/orders", headers=AUTH).get_json()["items"][0]
    assert order["product_id"] is None and order["product_name"] == "Landing"


def test_order_for_unknown_or_inactive_product_is_rejected(db_client):
    unknown = db_client.post("/api/public/orders", json={
        **ORDER, "product_id": "00000000-0000-0000-0000-000000000000"})
    assert unknown.status_code == 422
    assert "product_id" in unknown.get_json()["error"]["fields"]

    product = make_product(db_client)
    db_client.put(f"/api/admin/products/{product['id']}", headers=AUTH, json={"is_active": False})
    assert db_client.post("/api/public/orders", json={**ORDER, "product_id": product["id"]}).status_code == 422


def test_message_flow(db_client):
    res = db_client.post("/api/public/messages", json={
        "name": "O'Brien", "email": "ob@example.com", "subject": "Hi", "body": "Hello; DROP TABLE x;--", "lang": "en"})
    assert res.status_code == 201

    listing = db_client.get("/api/admin/messages", headers=AUTH).get_json()
    message = listing["items"][0]
    assert listing["total"] == 1 and message["name"] == "O'Brien"
    assert message["body"] == "Hello; DROP TABLE x;--"  # stored verbatim as data

    assert db_client.get("/api/admin/summary", headers=AUTH).get_json()["new_messages"] == 1
    read = db_client.put(f"/api/admin/messages/{message['id']}", headers=AUTH, json={"status": "read"})
    assert read.get_json()["status"] == "read"
    assert db_client.get("/api/admin/summary", headers=AUTH).get_json()["new_messages"] == 0
    assert db_client.delete(f"/api/admin/messages/{message['id']}", headers=AUTH).status_code == 204
    assert db_client.get("/api/admin/messages", headers=AUTH).get_json()["total"] == 0


def test_pagination(db_client):
    for i in range(3):
        db_client.post("/api/public/messages", json={"name": f"n{i}", "email": "a@b.co", "body": "x"})
    page = db_client.get("/api/admin/messages?limit=2&offset=2", headers=AUTH).get_json()
    assert page["total"] == 3 and len(page["items"]) == 1
    assert db_client.get("/api/admin/messages?limit=abc", headers=AUTH).status_code == 422
