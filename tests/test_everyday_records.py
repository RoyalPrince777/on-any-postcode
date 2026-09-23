"""Offline SQLite persistence / canonical audit / fail-closed tests."""
import sqlite3
from datetime import datetime, timezone

import pytest

from oap.audit import initialize_audit_schema
from oap.everyday_records import (
    initialize_schema,
    propose_partner,
    propose_resource,
    records,
)


def database(tmp_path):
    path = tmp_path / "everyday.sqlite3"
    conn = sqlite3.connect(path)
    initialize_audit_schema(conn)
    conn.commit()
    initialize_schema(conn)
    conn.commit()
    return conn, path


def test_requires_existing_canonical_audit():
    conn = sqlite3.connect(":memory:")
    with pytest.raises(RuntimeError, match="canonical_audit_schema_required"):
        initialize_schema(conn)


def test_partner_persists_with_shared_audit_after_restart(tmp_path):
    conn, path = database(tmp_path)
    result = propose_partner(conn, record_id="p1", organisation="Local shop",
                             prize="Essentials voucher", actor="private-operator")
    assert result["status"] == "proposed_unverified"
    assert result["receipt_seq"] == 1
    conn.close()
    with sqlite3.connect(path) as recovered:
        result = records(recovered)
        assert result["partners"][0]["status"] == "proposed"
        assert result["partners"][0]["prize"] == "Essentials voucher"
        assert not result["public_listing_allowed"]
        assert recovered.execute("SELECT count(*) FROM audit_events").fetchone()[0] == 1


def test_resource_stays_private_and_stores_source_date(tmp_path):
    conn, path = database(tmp_path)
    result = propose_resource(conn, record_id="r1", title="Local help",
                              url="https://example.org/help", source="Source",
                              checked_on=datetime.now(timezone.utc).date().isoformat(),
                              actor="private-operator")
    assert result["published"] is False and result["receipt_seq"] == 1
    conn.close()
    with sqlite3.connect(path) as recovered:
        saved = records(recovered)["resources"][0]
        assert saved["status"] == "private_review"
        assert saved["checked_on"] == datetime.now(timezone.utc).date().isoformat()


def test_invalid_resource_rejected_before_write(tmp_path):
    conn, _ = database(tmp_path)
    for url in ("http://example.org", "https://user:pass@example.org",
                "file:///etc/passwd"):
        with pytest.raises(ValueError, match="invalid_private_resource"):
            propose_resource(conn, record_id="r1", title="Resource", url=url,
                             source="Source", checked_on=datetime.now(timezone.utc).date().isoformat(),
                             actor="private-operator")
    assert records(conn)["resources"] == []
    assert conn.execute("SELECT count(*) FROM audit_events").fetchone()[0] == 0


def test_duplicate_rolls_back_without_extra_audit(tmp_path):
    conn, _ = database(tmp_path)
    for index in range(2):
        if index:
            with pytest.raises(sqlite3.IntegrityError):
                propose_partner(conn, record_id="p1", organisation="Shop",
                                prize="Voucher", actor="operator")
        else:
            propose_partner(conn, record_id="p1", organisation="Shop",
                            prize="Voucher", actor="operator")
    assert len(records(conn)["partners"]) == 1
    assert conn.execute("SELECT count(*) FROM audit_events").fetchone()[0] == 1


def test_audit_write_failure_rolls_back_partner(tmp_path):
    conn, _ = database(tmp_path)
    conn.execute("DROP TABLE audit_events")
    conn.commit()
    with pytest.raises(sqlite3.OperationalError):
        propose_partner(conn, record_id="p1", organisation="Shop",
                        prize="Voucher", actor="operator")
    assert conn.execute("SELECT count(*) FROM everyday_partners").fetchone()[0] == 0
