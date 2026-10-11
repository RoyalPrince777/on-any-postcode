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
