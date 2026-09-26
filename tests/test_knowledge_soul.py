from contextlib import contextmanager
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from mission_control import knowledge_core


class _Result:
    def __init__(self, one=None):
        self.one = one

    def fetchone(self):
        return self.one


class _SoulConnection:
    def __init__(self):
        self.calls = []
        self.commits = 0

    def execute(self, sql, params=None):
        self.calls.append((sql, params))
        now = datetime(2026, 9, 26, tzinfo=timezone.utc)
        if "SELECT 1 FROM oap_knowledge_cards" in sql:
            return _Result((1,))
        if "INSERT INTO oap_knowledge_evidence" in sql:
            return _Result((uuid4(), now))
        return _Result((1,))

    def commit(self):
        self.commits += 1


def test_row_card_fails_closed_on_tampered_digest():
    now = datetime(2026, 9, 26, tzinfo=timezone.utc)
    with pytest.raises(
        knowledge_core.KnowledgeUnavailable,
        match="knowledge_card_integrity_failed",
    ):
        knowledge_core._row_card(
            (
                uuid4(),
                "Title",
                "Insight",
                None,
                "RAW",
                "PRIVATE",
                now,
                now,
                "0" * 64,
            )
        )


def test_recovery_receipt_requires_independent_durable_backend(monkeypatch):
    captured = {}

    def write(kind, payload, *, require_durable=False):
        captured["kind"] = kind
        captured["payload"] = payload
        captured["require_durable"] = require_durable
        return {
            "ok": True,
            "read_back_ok": True,
            "durable": True,
            "fallback_used": False,
            "backend": "independent_hrm_postgres",
            "receipt_id": "receipt-1",
            "status": "written_and_read_back",
        }

    monkeypatch.setattr(knowledge_core.smi_receipt_backend, "write_receipt", write)
    proof = knowledge_core._recovery_receipt(
        str(uuid4()),
        {
            "card_id": str(uuid4()),
            "content_digest": "a" * 64,
            "visibility": "PRIVATE",
            "evidence_state": "RAW",
        },
    )

    assert captured["kind"] == "oap_knowledge_recovery_anchor"
    assert captured["require_durable"] is True
    assert proof["durable"] is True
    assert proof["fallback_used"] is False


def test_recovery_outage_never_becomes_fake_green(monkeypatch):
    monkeypatch.setattr(
        knowledge_core.smi_receipt_backend,
        "write_receipt",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("down")),
    )
    proof = knowledge_core._recovery_receipt(
        str(uuid4()),
        {
            "card_id": str(uuid4()),
            "content_digest": "a" * 64,
            "visibility": "PRIVATE",
            "evidence_state": "RAW",
        },
    )
    assert proof["ok"] is False
    assert proof["durable"] is False
    assert proof["read_back_ok"] is False


def test_provenance_is_owner_scoped_and_does_not_certify(monkeypatch):
    identity = str(uuid4())
    card_id = str(uuid4())
    connection = _SoulConnection()

    @contextmanager
    def connect(*, readonly=False):
        assert readonly is False
        yield connection

    monkeypatch.setattr(knowledge_core.postgres_db, "connect", connect)

    evidence = knowledge_core.attach_provenance(
        identity,
        card_id,
        evidence_ref="registry:source-1",
        provenance="OAP Registry source receipt",
        digest="b" * 64,
    )

    assert evidence is not None
    assert evidence["certified"] is False
    assert evidence["public"] is False
    sql = "\n".join(query for query, _params in connection.calls)
    assert "owner_identity_id=%s" in sql
    assert "PROVENANCE_ATTACHED" in sql
    assert "CERTIFIED" not in sql
    assert connection.commits == 1


def test_bad_provenance_digest_fails_before_database(monkeypatch):
    monkeypatch.setattr(
        knowledge_core.postgres_db,
        "connect",
        lambda **_kwargs: pytest.fail("database must not be reached"),
    )
    with pytest.raises(ValueError, match="invalid_evidence_digest"):
        knowledge_core.attach_provenance(
            uuid4(),
            uuid4(),
            evidence_ref="registry:source-1",
            provenance="source",
            digest="not-a-digest",
        )
