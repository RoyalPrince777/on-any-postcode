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
