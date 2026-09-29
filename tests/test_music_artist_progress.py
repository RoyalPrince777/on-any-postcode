from flask import Flask

from mission_control import artist_progress, music_public_views, web_security


class _Result:
    def __init__(self, rows):
        self.rows = rows

    def fetchall(self):
        return self.rows

    def fetchone(self):
        return self.rows


class _Connection:
    def __init__(self):
        self.calls = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql, params=()):
        self.calls += 1
        if self.calls == 1:
            return _Result([
                (
                    "22222222-2222-4222-8222-222222222222",
                    "Local to Global",
                    "album",
                    "APPROVED",
                    "VERIFIED",
                    "PROVIDER_REQUIRED",
                    __import__("datetime").datetime(2026, 9, 29, tzinfo=__import__("datetime").timezone.utc),
                    8,
                )
            ])
        return _Result((1, 2, 1, 1500, 900, 600))


def test_artist_progress_is_evidence_backed(monkeypatch):
    monkeypatch.setattr(artist_progress.postgres_db, "connect", lambda **kwargs: _Connection())
    monkeypatch.setattr(
        artist_progress.music_engagement,
        "artist_audience",
        lambda identity_id: {
            "qualified_listens": 42,
            "listening_now": 3,
            "unique_qualified_listeners": 17,
            "music_qualified_views": 31,
            "tv_qualified_views": 19,
            "combined_reach": 24,
            "places": [
                {"country": "Ghana", "region": "Eastern", "borough": "Begoro", "unique_listeners": 5}
            ],
            "top_tracks": [],
        },
    )
    progress = artist_progress.artist_progress("11111111-1111-4111-8111-111111111111")
    assert progress["release_count"] == 1
    assert progress["track_count"] == 8
    assert progress["release_states"]["APPROVED"] == 1
    assert progress["rights_states"]["VERIFIED"] == 1
    assert progress["accounting"]["gross_active_minor"] == 1500
    assert progress["accounting"]["gross_reconciled_minor"] == 900
    assert progress["accounting"]["money_transfer_performed"] is False
    assert progress["qualified_listens"] == 42
    assert progress["listening_now"] == 3
    assert progress["combined_reach"] == 24
    assert progress["rank_position"] is None
    assert progress["radio_spins"] is None


def test_artist_progress_route_is_private_and_separate(monkeypatch):
    app = Flask(__name__, template_folder="../mission_control/templates")
    app.secret_key = "test"
    app.register_blueprint(music_public_views.bp)
    client = app.test_client()

    monkeypatch.setattr(web_security, "current_authenticated_user", lambda: None)
    blocked = client.get("/music/artist-progress")
    assert blocked.status_code in {302, 303}

    user = {
        "id": "11111111-1111-4111-8111-111111111111",
        "name": "Artist",
        "email": "",
        "email_verified": False,
    }
    monkeypatch.setattr(web_security, "current_authenticated_user", lambda: user)
    monkeypatch.setattr(music_public_views, "_identity", lambda sync=False: user["id"])
    monkeypatch.setattr(
        music_public_views.artist_progress,
        "artist_progress",
        lambda identity_id: {
            "surface": "Artist Progress",
            "release_count": 1,
            "track_count": 8,
            "release_states": {"APPROVED": 1},
            "rights_states": {"VERIFIED": 1},
            "releases": [
                {
                    "title": "Local to Global",
                    "release_type": "album",
                    "state": "APPROVED",
                    "rights_status": "VERIFIED",
                    "track_count": 8,
                }
            ],
            "accounting": {
                "currency": "GBP",
                "pending_reconciliation_count": 1,
                "reconciled_count": 2,
                "reversed_count": 0,
                "gross_active_minor": 1500,
                "gross_reconciled_minor": 900,
                "gross_reversed_minor": 0,
                "money_transfer_performed": False,
                "sika_execution_performed": False,
            },
            "qualified_listens": 42,
            "listening_now": 3,
            "unique_qualified_listeners": 17,
            "music_qualified_views": 31,
            "tv_qualified_views": 19,
            "combined_reach": 24,
            "places": [
                {"country": "Ghana", "region": "Eastern", "borough": "Begoro", "unique_listeners": 5}
            ],
            "top_tracks": [],
            "rank_position": None,
            "radio_spins": None,
            "audience_growth": None,
            "unavailable_metrics_reason": "rank_radio_growth_measurement_not_yet_proven",
            "human_authority_final": True,
        },
    )
    response = client.get("/music/artist-progress")
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "Artist Progress" in body
    assert "Local to Global" in body
    assert "no payout claim" in body
    assert "No simulated numbers." in body
