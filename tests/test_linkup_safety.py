from __future__ import annotations

import pytest

from mission_control import linkup_safety


def test_linkup_safety_schema_is_explicit_and_enforces_block_at_message_boundary():
    preview = linkup_safety.init_schema(dry_run=True)

    assert preview["applied"] is False
    sql = "\n".join(preview["statements"])
    assert "CREATE TABLE IF NOT EXISTS linkup_blocks" in sql
    assert "CREATE TABLE IF NOT EXISTS linkup_reports" in sql
    assert "BEFORE INSERT ON messages" in sql
    assert "linkup_blocked_pair" in sql


def test_linkup_safety_schema_requires_explicit_confirmation():
    with pytest.raises(PermissionError, match="explicit_confirmation_required"):
        linkup_safety.init_schema()


def test_linkup_block_and_report_reject_self_target_before_database_access():
    identity = "11111111-1111-4111-8111-111111111111"

    with pytest.raises(ValueError, match="cannot_block_self"):
        linkup_safety.block(identity, identity)
    with pytest.raises(ValueError, match="cannot_report_self"):
        linkup_safety.report(identity, identity, reason="safety")


def test_linkup_safety_routes_require_csrf_for_mutation(client):
    status = client.get("/linkup/safety/status")
    block = client.post("/linkup/blocks", json={"member_id": "x"})
    report = client.post(
        "/linkup/reports", json={"member_id": "x", "reason": "safety"}
    )

    assert status.status_code == 200
    assert status.headers["Cache-Control"] == "no-store"
    assert block.status_code == 403
    assert report.status_code == 403
