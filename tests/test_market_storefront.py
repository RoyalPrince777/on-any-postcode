from __future__ import annotations

import sqlite3

from flask import Flask

from market_storefront import register_market_storefront


def _app(tmp_path):
    database = tmp_path / "market.db"

    def db():
        conn = sqlite3.connect(database)
        conn.row_factory = sqlite3.Row
        return conn

    conn = db()
    conn.execute("""
        CREATE TABLE market_products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            price_minor INTEGER NOT NULL,
            currency TEXT NOT NULL DEFAULT 'GBP',
            image_url TEXT,
            seller_name TEXT,
            state TEXT NOT NULL,
            created_at TEXT
        )
    """)
    conn.commit()
    conn.close()

    app = Flask(__name__)
    app.secret_key = "test-secret"
    register_market_storefront(app, db)
    return app, db


def test_empty_market_is_truthful_and_shop_shaped(tmp_path):
    app, _ = _app(tmp_path)
    client = app.test_client()

    response = client.get("/market")

    assert response.status_code == 200
    assert b"OAP MARKET" in response.data
    assert b"Search products, sellers, categories" in response.data
    assert b"No live products match this view" in response.data
    assert b"Fake stock is not inserted" in response.data


def test_live_product_can_be_viewed_added_updated_and_removed(tmp_path):
    app, db = _app(tmp_path)
    conn = db()
    conn.execute(
        """INSERT INTO market_products
           (title,category,description,price_minor,currency,seller_name,state)
           VALUES (?,?,?,?,?,?,?)""",
        ("OAP Bandana", "Clothing", "First-party Market item", 2500, "GBP", "OAP", "LIVE"),
    )
    conn.commit()
    conn.close()

    client = app.test_client()

    shop = client.get("/market")
    assert b"OAP Bandana" in shop.data
    assert b"25.00" in shop.data

    detail = client.get("/market/product/1")
    assert detail.status_code == 200
    assert b"Add to bag" in detail.data

    added = client.post("/market/bag/add/1", data={"quantity": "2"}, follow_redirects=True)
    assert added.status_code == 200

    bag = client.get("/market/bag")
    assert b"OAP Bandana" in bag.data
    assert b"50.00" in bag.data
    assert b"Review checkout" in bag.data

    updated = client.post("/market/bag/update/1", data={"quantity": "1"}, follow_redirects=True)
    assert b"25.00" in updated.data

    removed = client.post(
        "/market/bag/update/1",
        data={"action": "remove"},
        follow_redirects=True,
    )
    assert b"Your bag is empty" in removed.data


def test_paused_products_are_not_public_or_addable(tmp_path):
    app, db = _app(tmp_path)
    conn = db()
    conn.execute(
        """INSERT INTO market_products
           (title,category,description,price_minor,currency,seller_name,state)
           VALUES (?,?,?,?,?,?,?)""",
        ("Hidden Item", "Clothing", "", 1000, "GBP", "OAP", "PAUSED"),
    )
    conn.commit()
    conn.close()

    client = app.test_client()
    assert b"Hidden Item" not in client.get("/market").data
    assert client.get("/market/product/1").status_code == 404
    assert client.post("/market/bag/add/1").status_code == 404


def test_checkout_does_not_fake_payment_execution(tmp_path):
    app, db = _app(tmp_path)
    conn = db()
    conn.execute(
        """INSERT INTO market_products
           (title,category,description,price_minor,currency,seller_name,state)
           VALUES (?,?,?,?,?,?,?)""",
        ("Live Item", "Creator Goods", "", 1200, "GBP", "Creator", "LIVE"),
    )
    conn.commit()
    conn.close()

    client = app.test_client()
    client.post("/market/bag/add/1")
    checkout = client.get("/market/checkout")

    assert checkout.status_code == 200
    assert b"Payment execution is intentionally not enabled" in checkout.data
    assert b"Supplier Bridge" in checkout.data
