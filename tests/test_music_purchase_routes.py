from flask import Flask

from mission_control import music_public_views, web_security


def _app():
    app = Flask(__name__)
    app.secret_key = "test"
    app.register_blueprint(music_public_views.bp)
    return app


def test_music_purchase_route_is_auth_and_csrf_bounded(monkeypatch):
    app = _app()
    client = app.test_client()

    monkeypatch.setattr(web_security, "current_authenticated_user", lambda: None)
    blocked = client.post("/music/api/purchases", json={})
    assert blocked.status_code == 401

    user = {
        "id": "11111111-1111-4111-8111-111111111111",
        "name": "OAP Member",
        "email": "",
        "email_verified": False,
    }
    monkeypatch.setattr(web_security, "current_authenticated_user", lambda: user)
    monkeypatch.setattr(web_security, "csrf_valid", lambda request: False)
    csrf = client.post("/music/api/purchases", json={})
    assert csrf.status_code == 403
    assert csrf.get_json()["error"]["code"] == "csrf_failed"


def test_music_purchase_route_creates_intent_without_claiming_capture(monkeypatch):
    app = _app()
    client = app.test_client()
    user = {
        "id": "11111111-1111-4111-8111-111111111111",
        "name": "OAP Member",
        "email": "",
        "email_verified": False,
    }
    monkeypatch.setattr(web_security, "current_authenticated_user", lambda: user)
    monkeypatch.setattr(web_security, "csrf_valid", lambda request: True)
    monkeypatch.setattr(music_public_views, "_identity", lambda sync=False: user["id"])
    monkeypatch.setattr(
        music_public_views._music_purchase_store,
        "create_intent",
        lambda **kwargs: {
            "purchase_id": "22222222-2222-4222-8222-222222222222",
            "item_type": "RELEASE",
            "item_id": kwargs["item_id"],
            "edition_type": "album",
            "amount_minor": 500,
            "currency": "GBP",
            "state": "PAYMENT_REQUIRED",
            "payment_capture_performed": False,
            "sika_execution_performed": False,
            "ownership_created": False,
        },
    )

    response = client.post(
        "/music/api/purchases",
        json={
            "item_type": "RELEASE",
            "item_id": "33333333-3333-4333-8333-333333333333",
            "edition_type": "album",
            "amount_minor": 500,
            "idempotency_key": "album-purchase-001",
        },
    )
    assert response.status_code == 201
    payload = response.get_json()
    assert payload["state"] == "PAYMENT_REQUIRED"
    assert payload["payment_capture_performed"] is False
    assert payload["sika_execution_performed"] is False
    assert payload["ownership_created"] is False


def test_my_music_reads_only_owned_items(monkeypatch):
    app = _app()
    client = app.test_client()
    user = {
        "id": "11111111-1111-4111-8111-111111111111",
        "name": "OAP Member",
        "email": "",
        "email_verified": False,
    }
    monkeypatch.setattr(web_security, "current_authenticated_user", lambda: user)
    monkeypatch.setattr(music_public_views, "_identity", lambda sync=False: user["id"])
    monkeypatch.setattr(
        music_public_views._music_purchase_store,
        "owned_items",
        lambda **kwargs: {
            "library": "My Music",
            "buyer_identity_id": kwargs["buyer_identity_id"],
            "items": [
                {
                    "ownership_id": "44444444-4444-4444-8444-444444444444",
                    "purchase_id": "22222222-2222-4222-8222-222222222222",
                    "item_type": "RELEASE",
                    "item_id": "33333333-3333-4333-8333-333333333333",
                    "edition_type": "album",
                    "owned_at": "2026-09-29T17:00:00+00:00",
                }
            ],
            "item_count": 1,
            "ownership_source": "settled_purchase",
            "payment_capture_performed": False,
            "sika_execution_performed": False,
        },
    )

    response = client.get("/music/api/my-music")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["library"] == "My Music"
    assert payload["item_count"] == 1
    assert payload["ownership_source"] == "settled_purchase"
    assert payload["payment_capture_performed"] is False
