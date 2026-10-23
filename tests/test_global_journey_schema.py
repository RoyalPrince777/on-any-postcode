"""Fail-closed checks for the opt-in Global Movement schema migration."""
from unittest.mock import patch

import pytest

from mission_control import global_journey_schema


def test_migration_requires_explicit_approval():
    with patch("mission_control.postgres_db.connect") as connect:
        with pytest.raises(RuntimeError, match="explicit_human_approval_required"):
            global_journey_schema.init_schema()
        connect.assert_not_called()


def test_dry_run_does_not_touch_database():
    with patch("mission_control.postgres_db.connect") as connect:
        result = global_journey_schema.init_schema(assume_yes=True, dry_run=True)
        assert result["dry_run"] is True
        assert result["checksum"] == global_journey_schema.CHECKSUM
        connect.assert_not_called()


def test_schema_enforces_unique_booking_and_restricts_deletion():
    ddl = "\n".join(global_journey_schema.STATEMENTS)
    assert "booking_id UUID NOT NULL UNIQUE" in ddl
    assert "ON DELETE RESTRICT" in ddl
    assert "owner_identity_id UUID NOT NULL" in ddl
    assert "CHECK (version = 1)" in ddl


class _ReadOnlyConnection:
    def __init__(self, checksum, table):
        self.checksum = checksum
        self.table = table
        self.queries = []

    def execute(self, query, params=None):
        self.queries.append((query, params))
        return self

    def fetchone(self):
        if len(self.queries) == 1:
            return None if self.checksum is None else (self.checksum,)
        return (self.table,)

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False


@pytest.mark.parametrize(
    ("checksum", "table", "ready"),
    [
        (global_journey_schema.CHECKSUM, "oap_global_journey_associations", True),
        (None, "oap_global_journey_associations", False),
        ("tampered", "oap_global_journey_associations", False),
        (global_journey_schema.CHECKSUM, None, False),
    ],
)
def test_schema_status_requires_verified_receipt_and_table(checksum, table, ready):
    connection = _ReadOnlyConnection(checksum, table)
    with patch("mission_control.postgres_db.connect", return_value=connection) as connect:
        assert global_journey_schema.schema_status()["schema_ready"] is ready
        connect.assert_called_once_with(readonly=True)


def test_schema_status_fails_closed_when_store_unavailable():
    with patch("mission_control.postgres_db.connect", side_effect=RuntimeError("offline")):
        assert global_journey_schema.schema_status() == {
            "schema_ready": False, "reason": "store_unavailable",
        }
