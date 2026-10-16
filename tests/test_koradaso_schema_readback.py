"""Schema readiness must fail closed when consent binding columns are absent."""
from contextlib import contextmanager

import pytest

from mission_control import koradaso_schema


class Cursor:
    def __init__(self, row):
        self.row = row

    def fetchone(self):
        return self.row


class ReadbackDB:
    def __init__(self, missing=()):
        self.missing = set(missing)

    def execute(self, sql, params=None):
        if "to_regclass" in sql:
            return Cursor(("present",))
        if "information_schema.columns" in sql:
            column = params[0]
            return Cursor(None if column in self.missing else (1,))
        raise AssertionError("Unexpected query")


@pytest.mark.parametrize(
    ("missing", "expected"),
    [
        ((), True),
        (("summary_hash",), False),
        (("claim_fingerprint",), False),
        (("summary_hash", "claim_fingerprint"), False),
    ],
)
def test_schema_readback_requires_both_consent_columns(monkeypatch, missing, expected):
    @contextmanager
    def connect(*args, **kwargs):
        assert kwargs.get("readonly") is True
        yield ReadbackDB(missing)

    monkeypatch.setattr(koradaso_schema.postgres_db, "connect", connect)
    result = koradaso_schema.readback()
    assert result["schema_ready"] is expected
    assert result["consent_columns"] == {
        "summary_hash": "summary_hash" not in missing,
        "claim_fingerprint": "claim_fingerprint" not in missing,
    }


def test_schema_readback_fails_closed_on_query_error(monkeypatch):
    @contextmanager
    def connect(*args, **kwargs):
        raise RuntimeError("database_unavailable")
        yield

    monkeypatch.setattr(koradaso_schema.postgres_db, "connect", connect)
    with pytest.raises(
        koradaso_schema.KoradasoSchemaUnavailable,
        match="koradaso_schema_readback_failed",
    ):
        koradaso_schema.readback()
