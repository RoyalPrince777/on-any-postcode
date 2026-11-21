"""Read-only cash site and staff evidence resolution."""
import pytest

from mission_control import sika_cash_authority_store as store
from mission_control.sika_cash_authority_boundary import CashAuthorityUnavailable


class Connection:
    def __init__(self, row):
        self.row = row
        self.queries = []

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def execute(self, sql, params):
        self.queries.append((sql, params))
        return self

    def fetchone(self):
        return self.row


def test_active_records_require_both_operator_and_site(monkeypatch):
    conn = Connection(("ACTIVE", True, True, "ACTIVE", True))
    monkeypatch.setattr(store.postgres_db, "connect", lambda *, readonly: conn)
    result = store.resolve_authority("site1", "operator1")
    assert result["staff_authorised"] is True
    assert result["site_verified"] is True
    assert result["regulated_cash_authority_proven"] is True
    assert conn.queries[0][1] == ("site1", "operator1")


@pytest.mark.parametrize("row", [
    ("SUSPENDED", True, True, "ACTIVE", True),
    ("ACTIVE", False, True, "ACTIVE", True),
    ("ACTIVE", True, False, "ACTIVE", True),
    ("ACTIVE", True, True, "REVOKED", True),
    ("ACTIVE", True, True, "ACTIVE", False),
])
def test_inactive_or_incomplete_records_do_not_grant_all_rights(monkeypatch, row):
    monkeypatch.setattr(store.postgres_db, "connect", lambda *, readonly: Connection(row))
    record = store.resolve_authority("site1", "operator1")
    assert not all(record[k] is True for k in (
        "staff_authorised", "site_verified", "regulated_cash_authority_proven"
    ))


def test_missing_or_offline_evidence_denied(monkeypatch):
    monkeypatch.setattr(store.postgres_db, "connect", lambda *, readonly: Connection(None))
    with pytest.raises(CashAuthorityUnavailable, match="cash_authority_records_missing"):
        store.resolve_authority("site1", "operator1")

    def offline(*, readonly):
        raise OSError("offline")

    monkeypatch.setattr(store.postgres_db, "connect", offline)
    with pytest.raises(CashAuthorityUnavailable, match="cash_authority_records_unavailable"):
        store.resolve_authority("site1", "operator1")


def test_schema_is_only_a_contract():
    assert len(store.SCHEMA_STATEMENTS) == 2
    assert all("CREATE TABLE" in statement for statement in store.SCHEMA_STATEMENTS)
