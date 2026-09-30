"""Radio discovery is station-scoped and never bypasses Music rights."""
from contextlib import contextmanager
from uuid import uuid4

from flask import Flask, render_template

from mission_control import music_public_views, radio_core


STATION, TRACK, ASSET = (str(uuid4()) for _ in range(3))


def _client():
    app = Flask(__name__, template_folder="../mission_control/templates")
    app.register_blueprint(music_public_views.bp)
    return app.test_client()


def test_public_discovery_filters_candidates_by_radio_rights(monkeypatch):
    monkeypatch.setattr(
        music_public_views._radio_store, "public_station_candidates",
        lambda: [{
            "station_id": STATION, "station_name": "Founder Station",
            "track_id": TRACK, "asset_id": ASSET,
            "delivery_authorized": False, "airplay_confirmed": False,
        }],
    )
    channels = []

    def gate(**kw):
        channels.append(kw)
        return {"allowed": False}

    monkeypatch.setattr(
        music_public_views._music_entitlement_store, "public_gate", gate
    )
    result = _client().get("/radio/api/stations")
    assert result.status_code == 200
    assert result.get_json()["stations"] == []
    assert channels == [
        {"asset_id": ASSET, "territory": "*", "channel": "OAP Radio"}
    ]


def test_public_discovery_only_builds_station_bound_audio_url(monkeypatch):
    monkeypatch.setattr(
        music_public_views._radio_store, "public_station_candidates",
        lambda: [{
            "station_id": STATION, "station_name": "Founder Station",
            "track_id": TRACK, "asset_id": ASSET,
        }],
    )
    monkeypatch.setattr(
        music_public_views._music_entitlement_store, "public_gate",
        lambda **kw: {"allowed": True},
    )
    response = _client().get("/radio/api/stations")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["continuous_broadcast_confirmed"] is False
    assert len(payload["stations"]) == 1
    item = payload["stations"][0]
    assert item["stream_url"] == (
        f"/radio/api/stations/{STATION}/tracks/{TRACK}/assets/{ASSET}/stream"
    )
    assert item["broadcast_live"] is False
    assert item["airplay_confirmed"] is False
    assert "owner_identity_id" not in item
    assert response.headers["Cache-Control"] == "no-store"


def test_radio_candidate_store_restricts_sql_to_public_eligible_rows(monkeypatch):
    query = []

    class Connection:
        def execute(self, sql):
            query.append(sql)
            return self

        def fetchall(self):
            return [(STATION, "Founder Station", TRACK, ASSET)]

    @contextmanager
    def connection(*, readonly=False):
        assert readonly is True
        yield Connection()

    monkeypatch.setattr(radio_core.postgres_db, "connect", connection)
    candidates = radio_core.RadioStore().public_station_candidates()
    assert candidates[0]["station_name"] == "Founder Station"
    assert candidates[0]["delivery_authorized"] is False
    assert candidates[0]["airplay_confirmed"] is False
    sql = query[0]
    for requirement in (
        "s.state='ACTIVE'", "s.founder_approved=TRUE",
        "c.stopped=FALSE", "c.always_on=TRUE", "a.stopped=FALSE",
        "r.owner_identity_id=s.owner_identity_id",
        "a.owner_identity_id=s.owner_identity_id",
        "ORDER BY position ASC LIMIT 1",
    ):
        assert requirement in sql


def test_radio_listener_uses_station_choices_not_generic_catalogue():
    app = Flask(__name__, template_folder="../mission_control/templates")
    with app.app_context():
        public = render_template("oap_radio.html", founder_control=False)
    assert 'id="listener-station-select"' in public
    assert "fetch('/radio/api/stations'" in public
    assert "fetch('/music/api/catalogue'" not in public
    assert "player.src=x.stream_url" in public
    assert "continuous broadcast not claimed" in public
    assert 'id="station-approve-button"' not in public
