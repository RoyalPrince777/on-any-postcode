"""Durable STOP, restart recovery, authority and audit failure tests."""
import sqlite3

import pytest

from oap.audit import initialize_audit_schema
from oap.raffles_durable import initialize_schema, set_stop, status


def database(tmp_path):
    path = tmp_path / "raffles.sqlite3"
    conn = sqlite3.connect(path)
    initialize_audit_schema(conn)
    conn.commit()
    initialize_schema(conn)
    conn.commit()
    return conn, path


def test_unknown_campaign_is_stopped_not_green(tmp_path):
    conn, _ = database(tmp_path)
    result = status(conn, "r1")
    assert result["stopped"] is True and not result["execution_granted"]


def test_stop_restart_and_authorised_recovery(tmp_path):
    conn, path = database(tmp_path)
    first = set_stop(conn, campaign_id="r1", actor="operator", action="STOP")
    assert first["outcome"] == "STOPPED" and first["receipt_seq"] == 1
    conn.close()
    with sqlite3.connect(path) as reopened:
        assert status(reopened, "r1")["stopped"]
        with pytest.raises(PermissionError, match="canonical_founder_authority_required"):
            set_stop(reopened, campaign_id="r1", actor="operator", action="RECOVER")
        assert status(reopened, "r1")["stopped"]
        recovered = set_stop(
            reopened, campaign_id="r1", actor="authority-uuid", action="RECOVER",
            authority_checker=lambda actor: actor == "authority-uuid")
        assert recovered["outcome"] == "RECOVERED_TO_REVIEW"
        assert not recovered["stopped"] and not recovered["execution_granted"]
        assert reopened.execute("SELECT count(*) FROM audit_events").fetchone()[0] == 2


def test_missing_audit_rejects_schema_and_stop():
    conn = sqlite3.connect(":memory:")
    with pytest.raises(RuntimeError, match="canonical_audit_schema_required"):
        initialize_schema(conn)
    with pytest.raises(RuntimeError, match="canonical_audit_schema_required"):
        set_stop(conn, campaign_id="r1", actor="operator", action="STOP")


def test_audit_failure_rolls_back_stop(tmp_path):
    conn, _ = database(tmp_path)
    conn.execute("DROP TABLE audit_events")
    conn.commit()
    with pytest.raises(RuntimeError, match="canonical_audit_schema_required"):
        set_stop(conn, campaign_id="r1", actor="operator", action="STOP")
    assert conn.execute("SELECT count(*) FROM raffles_stop_state").fetchone()[0] == 0


def test_invalid_actions_and_authority_fail_closed(tmp_path):
    conn, _ = database(tmp_path)
    with pytest.raises(ValueError, match="invalid_raffles_stop_command"):
        set_stop(conn, campaign_id="r1", actor="operator", action="PUBLISH")
    with pytest.raises(PermissionError):
        set_stop(conn, campaign_id="r1", actor="operator", action="RECOVER",
                 authority_checker=lambda _actor: False)
    assert status(conn, "r1")["stopped"]


def test_explicit_schema_is_never_created_at_import(tmp_path):
    path = tmp_path / "empty.db"
    with sqlite3.connect(path) as conn:
        initialize_audit_schema(conn)
        conn.commit()
        with pytest.raises(sqlite3.OperationalError):
            status(conn, "r1")
