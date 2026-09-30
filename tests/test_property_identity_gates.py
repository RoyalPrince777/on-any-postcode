"""Property identity adapter checks against existing canonical services.

Mocks model canonical response boundaries, not live property authority evidence.
"""
import uuid
from contextlib import contextmanager

from mission_control import property_identity_gates as gates


def test_certified_merchant_uses_canonical_status(monkeypatch):
    identity = str(uuid.uuid4())
    calls = []
    def status(value):
        calls.append(value)
        return {"merchant": True}
    monkeypatch.setattr(gates.certification, "identity_status", status)
    assert gates.certified_merchant(identity) is True
    assert calls == [identity]
    monkeypatch.setattr(gates.certification, "identity_status", lambda _: {"merchant": False})
    assert gates.certified_merchant(identity) is False


def test_certification_missing_invalid_or_outage_denies(monkeypatch):
    identity = str(uuid.uuid4())
    assert gates.certified_merchant("not-an-identity") is False
    monkeypatch.setattr(gates.certification, "identity_status", lambda _: {})
    assert gates.certified_merchant(identity) is False
    def offline(_):
        raise gates.certification.CertificationUnavailable("offline")
    monkeypatch.setattr(gates.certification, "identity_status", offline)
    assert gates.certified_merchant(identity) is False


def test_reviewer_uses_existing_level_zero_human_authority(monkeypatch):
    reviewer = str(uuid.uuid4())
    publisher = str(uuid.uuid4())
    calls = []
    @contextmanager
    def connect(*, readonly):
        assert readonly is True
        yield "canonical-connection"
    def require(connection, identity):
        calls.append((connection, identity))
        return {"is_human_authority": True}
    monkeypatch.setattr(gates.postgres_db, "connect", connect)
    monkeypatch.setattr(gates.authority, "require_human_authority", require)
    assert gates.independent_human_reviewer(reviewer, publisher) is True
    assert calls == [("canonical-connection", reviewer)]
    assert gates.independent_human_reviewer(reviewer, reviewer) is False
    assert gates.independent_human_reviewer("invalid", publisher) is False
    assert len(calls) == 1


def test_revoked_reviewer_or_store_outage_denies(monkeypatch):
    reviewer = str(uuid.uuid4())
    publisher = str(uuid.uuid4())
    @contextmanager
    def connect(*, readonly):
        yield "canonical-connection"
    monkeypatch.setattr(gates.postgres_db, "connect", connect)
    def revoked(*_):
        raise gates.authority.HumanAuthorityRequired("revoked")
    monkeypatch.setattr(gates.authority, "require_human_authority", revoked)
    assert gates.independent_human_reviewer(reviewer, publisher) is False
    def unavailable(*, readonly):
        raise RuntimeError("unavailable")
    monkeypatch.setattr(gates.postgres_db, "connect", unavailable)
    assert gates.independent_human_reviewer(reviewer, publisher) is False
