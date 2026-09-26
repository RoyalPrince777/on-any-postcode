import pytest
from flask import Flask

from mission_control import music_civilization_migration, music_public_views


def test_public_music_route_is_real_and_truth_mode():
    app = Flask(__name__, template_folder="../mission_control/templates")
    app.register_blueprint(music_public_views.bp)
    client = app.test_client()
    response = client.get("/music")
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "OAP Music" in body
    assert "No publicly cleared playable track is available yet." in body
    assert "Playback stays locked" in body


def test_music_migration_requires_explicit_approval():
    with pytest.raises(RuntimeError, match="Explicit human approval required"):
        music_civilization_migration.apply()


def test_music_migration_versions_are_ordered_and_complete():
    assert [version for version, _ in music_civilization_migration._MIGRATIONS] == [
        "0007_oap_music_evidence_chain",
        "0008_oap_radio_core",
        "0009_oap_records_archive",
        "0010_oap_live_music",
        "0011_oap_music_recovery_manifest",
        "0012_oap_music_acceptance_receipts",
    ]
