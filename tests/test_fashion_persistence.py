"""Bounded tests for staged Fashion storage; never touch a real database."""
from contextlib import contextmanager

import pytest

from mission_control import fashion_persistence
from mission_control.fashion_first_party import (
    FashionDraft,
    FashionError,
    FashionVariant,
)

OWNER = "11111111-1111-4111-8111-111111111111"
OTHER = "22222222-2222-4222-8222-222222222222"
PRODUCT = "33333333-3333-4333-8333-333333333333"


def draft():
    return FashionDraft(
        OWNER, PRODUCT, "OAP Hoodie", "hoodie", "oap:art/001",
        True, True, (FashionVariant("OAP-HOODIE-001", "L", "Black", 3500),),
    )


@pytest.fixture(autouse=True)
def current_merchant(monkeypatch):
    monkeypatch.setattr(
        fashion_persistence.certification, "identity_status",
        lambda identity_id: {"merchant": identity_id == OWNER},
    )


class FakeConnection:
    def __init__(self, *, product=True, revision=0):
        self.product = product
        self.revision = revision
        self.stored = None
        self.calls = []
        self.commits = 0

    def execute(self, statement, params):
        self.calls.append((statement, params))
        if "FROM products" in statement:
            self.result = (1,) if self.product else None
        elif "INSERT INTO oap_fashion_snapshots" in statement:
            if self.revision == 0:
                self.revision = 1
                self.stored = params[2]
                self.result = (1,)
            else:
                self.result = None
        elif "UPDATE oap_fashion_snapshots" in statement:
            if self.revision == params[3]:
                self.revision += 1
                self.stored = params[0]
                self.result = (self.revision,)
            else:
                self.result = None
        elif "SELECT snapshot_json,version" in statement:
            self.result = (self.stored, self.revision) if self.stored else None
        else:
            raise AssertionError("Unexpected SQL")
        return self

    def fetchone(self):
        return self.result

    def commit(self):
        self.commits += 1


def install(monkeypatch, connection):
    @contextmanager
    def connect(*, readonly=False):
        yield connection

    monkeypatch.setattr(fashion_persistence.postgres_db, "connect", connect)


def test_create_read_update_and_revision_conflict(monkeypatch):
    c = FakeConnection()
    install(monkeypatch, c)
    p = draft()
    assert fashion_persistence.save_fashion(
        actor_id=OWNER, draft=p, expected_revision=0
    ) == 1
    loaded, revision = fashion_persistence.read_fashion(
        actor_id=OWNER, product_id=PRODUCT
    )
    assert loaded.variants == p.variants
    assert revision == 1
    p.submit_review(OWNER, "review")
    assert fashion_persistence.save_fashion(
        actor_id=OWNER, draft=p, expected_revision=1
    ) == 2
    with pytest.raises(FashionError, match="fashion_revision_conflict"):
        fashion_persistence.save_fashion(
            actor_id=OWNER, draft=p, expected_revision=1
        )
    assert c.commits == 2


def test_foreign_owner_rejected_before_database_connection(monkeypatch):
    def forbidden(*, readonly=False):
        raise AssertionError("No DB calls")

    monkeypatch.setattr(fashion_persistence.postgres_db, "connect", forbidden)
    with pytest.raises(FashionError, match="not_product_owner"):
        fashion_persistence.save_fashion(
            actor_id=OTHER, draft=draft(), expected_revision=0
        )


def test_market_product_must_be_owned(monkeypatch):
    c = FakeConnection(product=False)
    install(monkeypatch, c)
    with pytest.raises(FashionError, match="owned_market_product_not_found"):
        fashion_persistence.save_fashion(
            actor_id=OWNER, draft=draft(), expected_revision=0
        )
    assert c.commits == 0


def test_existing_product_not_overwritten_by_create(monkeypatch):
    c = FakeConnection(revision=1)
    install(monkeypatch, c)
    with pytest.raises(FashionError, match="fashion_revision_conflict"):
        fashion_persistence.save_fashion(
            actor_id=OWNER, draft=draft(), expected_revision=0
        )
    assert c.commits == 0


def test_read_fail_closed_when_snapshot_missing(monkeypatch):
    c = FakeConnection()
    install(monkeypatch, c)
    with pytest.raises(FashionError, match="fashion_snapshot_not_found"):
        fashion_persistence.read_fashion(actor_id=OWNER, product_id=PRODUCT)


def test_invalid_revision_does_not_connect(monkeypatch):
    with pytest.raises(FashionError, match="invalid_fashion_revision"):
        fashion_persistence.save_fashion(
            actor_id=OWNER, draft=draft(), expected_revision=-1
        )


def test_staged_migration_is_not_executed():
    assert fashion_persistence.FASHION_MIGRATION_VERSION == "0007_first_party_fashion"
    assert all("IF NOT EXISTS" in statement for statement in
               fashion_persistence.FASHION_SCHEMA_STATEMENTS)


def test_revoked_certification_blocks_save_before_database(monkeypatch):
    monkeypatch.setattr(
        fashion_persistence.certification, "identity_status",
        lambda identity_id: {"merchant": False},
    )
    with pytest.raises(FashionError, match="certified_merchant_required"):
        fashion_persistence.save_fashion(
            actor_id=OWNER, draft=draft(), expected_revision=0
        )


def test_certification_store_unavailable_fails_closed(monkeypatch):
    def unavailable(identity_id):
        raise fashion_persistence.certification.CertificationUnavailable("down")

    monkeypatch.setattr(
        fashion_persistence.certification, "identity_status", unavailable
    )
    with pytest.raises(FashionError, match="merchant_certification_unavailable"):
        fashion_persistence.save_fashion(
            actor_id=OWNER, draft=draft(), expected_revision=0
        )


def test_corrupt_json_snapshot_fails_closed(monkeypatch):
    c = FakeConnection(revision=1)
    c.stored = "{invalid-json"
    install(monkeypatch, c)
    with pytest.raises(FashionError, match="invalid_fashion_snapshot"):
        fashion_persistence.read_fashion(actor_id=OWNER, product_id=PRODUCT)
