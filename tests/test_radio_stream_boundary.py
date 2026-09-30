"""Radio audio requests preserve the shared Music gates and enforce station STOP."""
from uuid import uuid4

from flask import Flask

from mission_control import music_public_views

STATION, TRACK, ASSET, OWNER = (str(uuid4()) for _ in range(4))
PATH = f"/radio/api/stations/{STATION}/tracks/{TRACK}/assets/{ASSET}/stream"


def _app():
    app = Flask(__name__)
    app.register_blueprint(music_public_views.bp)
    return app.test_client()


def test_radio_stream_fails_closed_before_rights_if_station_stopped(monkeypatch):
    monkeypatch.setattr(
        music_public_views._radio_store, "delivery_preflight", lambda **kw: False
    )

    def no_rights(**kw):
        raise AssertionError("STOP must block rights/delivery")

    monkeypatch.setattr(
        music_public_views._music_entitlement_store, "public_gate", no_rights
    )
    response = _app().get(PATH)
    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "radio_playout_locked"


def test_radio_stream_rechecks_stop_after_read_and_uses_radio_channel(monkeypatch):
    decisions = iter((True, False))
    monkeypatch.setattr(
        music_public_views._radio_store,
        "delivery_preflight",
        lambda **kw: next(decisions),
    )
    channels = []

    def rights(**kw):
        channels.append(kw["channel"])
        return {
            "allowed": True,
            "owner_identity_id": OWNER,
            "rights_decision_hash": "a" * 64,
            "entitlement_id": str(uuid4()),
        }

    monkeypatch.setattr(music_public_views._music_entitlement_store, "public_gate", rights)
    monkeypatch.setattr(
        music_public_views._music_asset_store,
        "read_public_candidate",
        lambda **kw: (OWNER, b"0123456789", "audio/mpeg", "b" * 64, "track.mp3"),
    )
    response = _app().get(PATH)
    assert channels == ["OAP Radio"]
    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "radio_playout_locked"
    assert response.data != b"0123456789"


def test_radio_stream_requires_radio_rights_and_entitlement(monkeypatch):
    monkeypatch.setattr(
        music_public_views._radio_store, "delivery_preflight", lambda **kw: True
    )

    def locked(**kw):
        assert kw["channel"] == "OAP Radio"
        return {"allowed": False}

    monkeypatch.setattr(music_public_views._music_entitlement_store, "public_gate", locked)
    response = _app().get(PATH)
    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "public_playback_locked"


def test_radio_range_bytes_do_not_claim_airplay(monkeypatch):
    calls = []

    def preflight(**kw):
        calls.append(kw)
        return True

    monkeypatch.setattr(music_public_views._radio_store, "delivery_preflight", preflight)
    admissions = []

    def admit(**kw):
        admissions.append(kw)
        return "44444444-4444-4444-8444-444444444444"

    monkeypatch.setattr(music_public_views._radio_store, "admit_delivery", admit)
    monkeypatch.setattr(
        music_public_views._music_entitlement_store,
        "public_gate",
        lambda **kw: {
            "allowed": True,
            "owner_identity_id": OWNER,
            "rights_decision_hash": "a" * 64,
            "entitlement_id": str(uuid4()),
        },
    )
    monkeypatch.setattr(
        music_public_views._music_asset_store,
        "read_public_candidate",
        lambda **kw: (OWNER, b"0123456789", "audio/mpeg", "b" * 64, "track.mp3"),
    )
    response = _app().get(PATH, headers={"Range": "bytes=2-5"})
    assert response.status_code == 206
    assert response.data == b"2345"
    assert len(calls) == 2
    assert len(admissions) == 1
    assert admissions[0]["prepared_bytes"] == 4
    assert admissions[0]["response_status"] == 206
    assert admissions[0]["station_id"] == STATION
    assert admissions[0]["media_sha256"] == "b" * 64
    assert all(
        c == {"station_id": STATION, "track_id": TRACK, "asset_id": ASSET}
        for c in calls
    )
    assert response.headers["X-OAP-Radio-Station"] == STATION
    assert response.headers["X-OAP-Airplay-Confirmed"] == "false"
    assert response.headers["X-OAP-Receipt-Type"] == "RESPONSE_PREPARED"
    assert response.headers["X-OAP-Delivery-Admission"] == (
        "44444444-4444-4444-8444-444444444444"
    )
    assert response.headers["Cache-Control"] == "no-store"


def test_radio_admission_rejects_stop_after_preflight_without_returning_bytes(monkeypatch):
    monkeypatch.setattr(
        music_public_views._radio_store, "delivery_preflight", lambda **kw: True
    )
    monkeypatch.setattr(
        music_public_views._radio_store, "admit_delivery", lambda **kw: None
    )
    monkeypatch.setattr(
        music_public_views._music_entitlement_store, "public_gate",
        lambda **kw: {
            "allowed": True,
            "owner_identity_id": OWNER,
            "rights_decision_hash": "a" * 64,
            "entitlement_id": "33333333-3333-4333-8333-333333333333",
        },
    )
    monkeypatch.setattr(
        music_public_views._music_asset_store, "read_public_candidate",
        lambda **kw: (OWNER, b"0123456789", "audio/mpeg", "b" * 64, "track.mp3"),
    )
    response = _app().get(PATH)
    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "radio_playout_locked"
    assert "X-OAP-Delivery-Admission" not in response.headers
    assert response.data != b"0123456789"
