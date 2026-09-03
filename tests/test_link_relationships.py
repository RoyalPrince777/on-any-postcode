from __future__ import annotations

import pytest

from mission_control import link_relationships


def test_link_relationship_schema_is_explicit_and_minimal():
    preview = link_relationships.init_schema(dry_run=True)
    sql = "\n".join(preview["statements"])
    assert preview["applied"] is False
    assert "CREATE TABLE IF NOT EXISTS link_requests" in sql
    assert "requester_id <> recipient_id" in sql
    assert "ux_link_requests_pending_pair" in sql
    assert "ux_link_requests_accepted_pair" in sql
    assert "CREATE TABLE IF NOT EXISTS conversations" not in sql
    assert "CREATE TABLE IF NOT EXISTS links" not in sql


def test_link_relationship_schema_requires_explicit_confirmation():
    with pytest.raises(PermissionError, match="explicit_confirmation_required"):
        link_relationships.init_schema()


def test_link_request_rejects_self_before_database(monkeypatch):
    identity = "11111111-1111-4111-8111-111111111111"
    monkeypatch.setattr(
        link_relationships.postgres_db,
        "connect",
        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("database should not open")),
    )
    with pytest.raises(ValueError, match="cannot_link_self"):
        link_relationships.request_link(identity, identity)


def test_link_response_rejects_unknown_decision_before_database():
    identity = "11111111-1111-4111-8111-111111111111"
    request_id = "22222222-2222-4222-8222-222222222222"
    with pytest.raises(ValueError, match="invalid_link_decision"):
        link_relationships.respond(identity, request_id, "maybe")
