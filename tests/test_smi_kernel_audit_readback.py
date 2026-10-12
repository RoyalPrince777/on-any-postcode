"""Fail-closed audit readback contracts with no real database or credentials."""

import uuid
from contextlib import contextmanager
from unittest.mock import patch

from mission_control.smi_kernel_audit_readback import readback_kernel_audit

IDENTITY = str(uuid.uuid4())
REQUEST = str(uuid.uuid4())


class Connection:
    def __init__(self, rows):
        self.rows = rows

    def execute(self, sql, params):
        assert params == (REQUEST,)
        assert "audit_events" in sql
        return self

    def fetchall(self):
        return self.rows


@contextmanager
def connect(rows):
    yield Connection(rows)


def read(rows):
    with (
        patch(
            "mission_control.smi_kernel_audit_readback.postgres_db.connect",
            side_effect=lambda readonly: connect(rows),
        ),
        patch(
            "mission_control.smi_kernel_audit_readback.authority.require_human_authority"
        ),
    ):
        return readback_kernel_audit(identity_id=IDENTITY, request_id=REQUEST)


def row(action="FOUNDER_TOOL_KERNEL_EXECUTED", executed=True):
    return (
        uuid.uuid4(), action, IDENTITY, REQUEST,
        {"request_id": REQUEST, "executed": executed,
         "receipt_id": "receipt", "sovereign_policy_fingerprint": "policy"},
    )


def test_matching_executed_row_is_audit_verified_not_hrm_durable():
    result = read([row()])
    assert result.verified and result.executed
    assert not result.durable_hrm_receipt_proven


def test_blocked_row_is_not_execution():
    result = read([row("FOUNDER_TOOL_KERNEL_BLOCKED", False)])
    assert result.verified and not result.executed


def test_missing_or_ambiguous_rows_fail_closed():
    assert not read([]).verified
    assert not read([row(), row()]).verified


def test_mismatched_actor_fails_closed():
    bad = list(row())
    bad[2] = "other"
    assert not read([tuple(bad)]).verified


def test_invalid_id_fails_closed():
    assert not readback_kernel_audit(
        identity_id=IDENTITY, request_id="not-uuid"
    ).verified
