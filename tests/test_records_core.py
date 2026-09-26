from uuid import uuid4

import pytest

from mission_control import entertainment_catalogue, records_core


def test_records_schema_binds_archive_to_music_and_evidence():
    sql = "\n".join(records_core.SCHEMA_STATEMENTS)
    assert "oap_records_masters" in sql
    assert "REFERENCES oap_music_releases(release_id)" in sql
    assert "REFERENCES oap_music_tracks(track_id)" in sql
    assert "REFERENCES oap_music_evidence_receipts(receipt_id)" in sql
    assert "oap_records_credits" in sql
    assert "oap_records_receipts" in sql


def test_records_contract_reuses_universal_player_and_stays_fail_closed():
    result = records_core.records_contract()
    assert result["canonical_release_owner"] == "OAP Music"
    assert result["player"]["owner"] == entertainment_catalogue.PLAYER_OWNER
    assert result["playback_enabled"] is False
    assert result["external_distribution_enabled"] is False
    assert result["rights_verified_by_records"] is False


def test_records_archive_gate_requires_private_music_handoff():
    blocked = records_core.archive_gate({"private_handoff_ready": False})
    ready = records_core.archive_gate({"private_handoff_ready": True})
    assert blocked["private_archive_ready"] is False
    assert ready["private_archive_ready"] is True
    assert ready["public_archive_ready"] is False
    assert ready["playback_enabled"] is False


def test_records_master_rejects_cross_owner_track(monkeypatch):
    owner, release, track = str(uuid4()), str(uuid4()), str(uuid4())

    class Result:
        def fetchone(self):
            return None

    class Connection:
        def __enter__(self):
            return self
        def __exit__(self, *_args):
            return False
        def execute(self, _sql, _params=()):
            return Result()
        def commit(self):
            raise AssertionError("no commit after ownership failure")

    monkeypatch.setattr(records_core.postgres_db, "connect", lambda **_kwargs: Connection())
    with pytest.raises(PermissionError, match="records_release_or_track_not_owned"):
        records_core.RecordsStore().create_master(
            owner_identity_id=owner,
            release_id=release,
            track_id=track,
            version_label="Original master",
        )


def test_records_receipt_never_claims_external_delivery(monkeypatch):
    owner, release = str(uuid4()), str(uuid4())
    receipt = str(uuid4())

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
            if "SELECT 1 FROM oap_music_releases" in sql:
                return Result((1,))
            return Result((receipt,))
        def commit(self):
            return None

    monkeypatch.setattr(records_core.postgres_db, "connect", lambda **_kwargs: Connection())
    result = records_core.RecordsStore().append_receipt(
        owner_identity_id=owner,
        release_id=release,
        receipt_kind="INTERNAL_ARCHIVE",
        destination="OAP Records",
        reference="archive-readback-1",
    )
    assert result["proves_external_distribution"] is False
