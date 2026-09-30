import pytest
from flask import Flask, render_template

from mission_control import product_cores, radio_core

RELEASE = "11111111-1111-4111-8111-111111111111"
OWNER = "22222222-2222-4222-8222-222222222222"
STATION = "33333333-3333-4333-8333-333333333333"


def test_founder_approval_requires_verified_rights(monkeypatch):
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
        def execute(self, sql, _params=()):
            if sql.startswith("UPDATE oap_music_releases"):
                return Result(None)
            if "SELECT state,rights_status" in sql:
                return Result(("REVIEW_REQUIRED", "REVIEW_REQUIRED"))
            return Result(None)
        def commit(self):
            raise AssertionError("must not commit unverified approval")

    monkeypatch.setattr(product_cores.postgres_db, "connect", lambda **_kwargs: Connection())
    with pytest.raises(PermissionError, match="verified_rights_required"):
        product_cores.PostgresProductCoreStore().founder_approve_release(
            release_id=RELEASE
        )


def test_founder_approval_records_approved_without_publishing(monkeypatch):
    class Instant:
        def isoformat(self):
            return "2026-09-29T13:30:00+00:00"

    class Result:
        def fetchone(self):
            return (
                RELEASE,
                OWNER,
                "Release",
                "single",
                "APPROVED",
                "VERIFIED",
                Instant(),
            )

    class Connection:
        committed = False
        def __enter__(self):
            return self
        def __exit__(self, *_args):
            return False
        def execute(self, sql, _params=()):
            assert "rights_status='VERIFIED'" in sql
            return Result()
        def commit(self):
            self.committed = True

    monkeypatch.setattr(product_cores.postgres_db, "connect", lambda **_kwargs: Connection())
    result = product_cores.PostgresProductCoreStore().founder_approve_release(
        release_id=RELEASE
    )
    assert result["state"] == "APPROVED"
    assert result["rights_status"] == "VERIFIED"
    assert result["founder_approval_recorded"] is True
    assert result["published"] is False
    assert result["external_distribution_performed"] is False


def test_radio_always_on_persists_mode_without_fake_broadcast(monkeypatch):
    class Result:
        def fetchone(self):
            return (STATION, True, True, False)

    class Connection:
        def __enter__(self):
            return self
        def __exit__(self, *_args):
            return False
        def execute(self, sql, params=()):
            assert "SET always_on=%s" in sql
            assert params[-2:] == (STATION, OWNER)
            return Result()
        def commit(self):
            pass

    monkeypatch.setattr(radio_core.postgres_db, "connect", lambda **_kwargs: Connection())
    result = radio_core.RadioStore().set_always_on(
        owner_identity_id=OWNER,
        station_id=STATION,
        enabled=True,
        auto_add_approved=True,
    )
    assert result["always_on"] is True
    assert result["operating_mode"] == "ALWAYS_ON"
    assert result["stopped"] is False
    assert result["background_daemon_claimed"] is False
    assert result["public_broadcast_claimed"] is False


def test_radio_always_on_has_separate_governed_migration():
    assert radio_core.RADIO_ALWAYS_ON_MIGRATION_VERSION == "0016_oap_radio_always_on"
    schema = "\n".join(radio_core.RADIO_ALWAYS_ON_SCHEMA_STATEMENTS)
    assert "ADD COLUMN IF NOT EXISTS always_on BOOLEAN" in schema
    assert "ADD COLUMN IF NOT EXISTS auto_add_approved BOOLEAN" in schema


def test_radio_founder_approval_controls_are_private_and_use_real_actions():
    app = Flask(__name__, template_folder="../mission_control/templates")
    with app.app_context():
        public = render_template("oap_radio.html", founder_control=False)
        private = render_template("oap_radio.html", founder_control=True)
    for control in ('id="station-approve-button"', 'id="show-form"',
                    'id="show-select"', 'id="show-approve-button"'):
        assert control not in public
        assert control in private
    assert "Approve Station" in private
    assert "Approve Show" in private
    assert "'/approve','POST'" in private
    assert "'/shows/'+encodeURIComponent(show)+'/approve','POST'" in private
    assert "Approved is not broadcast" in private
