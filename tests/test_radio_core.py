from uuid import uuid4

from flask import Flask

from mission_control import entertainment_catalogue, product_core_views, radio_core


def test_radio_schema_is_first_party_owner_scoped_and_reuses_music_tracks():
    sql = "\n".join(radio_core.SCHEMA_STATEMENTS)
    assert "oap_radio_stations" in sql
    assert "oap_radio_shows" in sql
    assert "oap_radio_schedule" in sql
    assert "oap_radio_rotation" in sql
    assert "owner_identity_id UUID NOT NULL REFERENCES users(id)" in sql
    assert "REFERENCES oap_music_tracks(track_id)" in sql


def test_radio_contract_reuses_one_universal_player_and_stays_fail_closed():
    result = radio_core.radio_contract()
    assert result["organ"] == "OAP Radio"
    assert result["music_source"] == "OAP Music"
    assert result["player"]["owner"] == entertainment_catalogue.PLAYER_OWNER
    assert result["dedicated_media_player_created"] is False
    assert result["broadcast_enabled"] is False
    assert result["public_streaming_enabled"] is False
    assert result["external_distribution_enabled"] is False


def test_station_projection_allowlists_metadata_without_stream_claim():
    station_id = str(uuid4())
    result = radio_core.station_projection(
        {
            "station_id": station_id,
            "name": "South London Radio",
            "state": "ACTIVE",
            "stream_url": "https://untrusted.example/live",
            "owner_identity_id": str(uuid4()),
        }
    )
    assert result == {
        "station_id": station_id,
        "name": "South London Radio",
        "state": "ACTIVE",
        "broadcast_live": False,
        "public_stream_url": None,
    }


def test_rotation_cannot_be_opened_by_caller_rights_flags():
    result = radio_core.rotation_gate(
        {
            "publication_state": "PUBLISHED",
            "rights_review_state": "VERIFIED",
            "rights_proof": True,
            "human_approval": True,
            "playback_enabled": True,
        }
    )
    assert result["rotation_eligible"] is False
    assert result["rights"]["allowed"] is False
    assert result["audio_fetch_performed"] is False
    assert result["broadcast_started"] is False
    assert result["human_authority_final"] is True


def test_radio_route_is_authenticated_read_only_contract():
    app = Flask(__name__)
    app.register_blueprint(product_core_views.bp, url_prefix="/mission/organs")
    rules = [rule for rule in app.url_map.iter_rules() if rule.rule == "/mission/organs/radio"]
    assert len(rules) == 1
    assert rules[0].methods == {"GET", "HEAD", "OPTIONS"}


def test_radio_schema_has_stop_state_and_activity_history_without_airplay_claim():
    sql = "\n".join(radio_core.SCHEMA_STATEMENTS)
    assert "oap_radio_station_control" in sql
    assert "stopped BOOLEAN NOT NULL DEFAULT TRUE" in sql
    assert "oap_radio_activity_events" in sql
    assert "ROTATION_QUEUED" in sql
    assert "STOPPED" in sql


def test_radio_store_rotation_requires_station_and_track_same_owner(monkeypatch):
    owner = str(uuid4())
    station = str(uuid4())
    track = str(uuid4())
    calls = []

    class Result:
        def __init__(self, row):
            self.row = row

        def fetchone(self):
            return self.row

    class Connection:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def execute(self, sql, params=()):
            calls.append((sql, params))
            if "FROM oap_radio_stations s" in sql:
                return Result(None)
            return Result((str(uuid4()),))

        def commit(self):
            raise AssertionError("must not commit when ownership proof fails")

    monkeypatch.setattr(radio_core.postgres_db, "connect", lambda **_kwargs: Connection())
    store = radio_core.RadioStore()
    import pytest

    with pytest.raises(PermissionError, match="radio_station_or_track_not_owned"):
        store.add_rotation(
            owner_identity_id=owner,
            station_id=station,
            track_id=track,
            position=1,
        )
    assert any("oap_music_releases" in sql for sql, _ in calls)


def test_radio_stop_is_fail_closed_and_cannot_claim_live(monkeypatch):
    owner = str(uuid4())
    station = str(uuid4())
    inserts = []

    class Result:
        def __init__(self, row):
            self.row = row

        def fetchone(self):
            return self.row

    class Connection:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def execute(self, sql, params=()):
            inserts.append((sql, params))
            if "UPDATE oap_radio_station_control" in sql:
                return Result((station,))
            return Result(None)

        def commit(self):
            return None

    monkeypatch.setattr(radio_core.postgres_db, "connect", lambda **_kwargs: Connection())
    result = radio_core.RadioStore().stop_station(
        owner_identity_id=owner,
        station_id=station,
        reason="Founder STOP",
    )
    assert result["stopped"] is True
    assert result["broadcast_enabled"] is False
    assert result["player_handoff_allowed"] is False
    assert any("'STOPPED'" in sql for sql, _ in inserts)


def test_radio_routes_cover_body_controls():
    app = Flask(__name__)
    app.register_blueprint(product_core_views.bp, url_prefix="/mission/organs")
    expected = {
        "/mission/organs/radio": {"GET", "HEAD", "OPTIONS"},
        "/mission/organs/radio/stations": {"POST", "OPTIONS"},
        "/mission/organs/radio/stations/<station_id>/shows": {"POST", "OPTIONS"},
        "/mission/organs/radio/stations/<station_id>/schedule": {"POST", "OPTIONS"},
        "/mission/organs/radio/stations/<station_id>/rotation": {"POST", "OPTIONS"},
        "/mission/organs/radio/stations/<station_id>/stop": {"POST", "OPTIONS"},
    }
    rules = {rule.rule: rule.methods for rule in app.url_map.iter_rules()}
    for path, methods in expected.items():
        assert rules[path] == methods
