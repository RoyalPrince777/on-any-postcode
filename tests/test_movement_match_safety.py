from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

import pytest

from mission_control import movement_match_safety

BOOKING = "00000000-0000-0000-0000-000000000101"
MEMBER = "00000000-0000-0000-0000-000000000102"
WORKER = "00000000-0000-0000-0000-000000000103"
PROPOSAL = "00000000-0000-0000-0000-000000000104"


class _Result:
    def __init__(self, row):
        self.row = row

    def fetchone(self):
        return self.row


class _Connection:
    def __init__(self, steps):
        self.steps = list(steps)
        self.committed = False
        self.queries: list[str] = []

    def execute(self, sql, params=()):
        del params
        self.queries.append(sql)
        if not self.steps:
            raise AssertionError(f"unexpected SQL: {sql}")
        expected, row = self.steps.pop(0)
        assert expected in sql
        return _Result(row)

    def commit(self):
        self.committed = True


def _connect(connection):
    @contextmanager
    def factory(*, readonly=False):
        del readonly
        yield connection

    return factory


def test_proposal_selection_requires_current_certification(monkeypatch):
    now = datetime.now(timezone.utc)
    connection = _Connection(
        [
            ("SELECT service_type,pickup,state", ("ride", {"zone": "CR4"}, "REQUESTED")),
            ("oap_identity_roles", (WORKER, "driver", "CR4")),
            (
                "INSERT INTO oap_movement_match_proposals",
                (PROPOSAL, WORKER, "driver", "PROPOSED", 1.0, "same_zone_certified_available", now),
            ),
            ("UPDATE oap_movement_bookings", None),
        ]
    )
    monkeypatch.setattr(
        movement_match_safety.postgres_db,
        "connect",
        _connect(connection),
    )

    result = movement_match_safety.SafePostgresMovementStore().propose_match(
        booking_id=BOOKING,
        member_identity_id=MEMBER,
    )

    assert result is not None
    assert result["worker_identity_id"] == WORKER
    assert result["current_certification_required"] is True
    assert result["dispatch_performed"] is False
    assert connection.committed is True


def test_accept_rejects_expired_availability_before_assignment(monkeypatch):
    expired = datetime.now(timezone.utc) - timedelta(seconds=1)
    connection = _Connection(
        [
            ("FROM oap_movement_match_proposals", (BOOKING, "driver", "PROPOSED")),
            ("FROM oap_movement_bookings", ("MATCH_PROPOSED",)),
            ("FROM oap_movement_availability", ("ONLINE", expired)),
        ]
    )
    monkeypatch.setattr(
        movement_match_safety.postgres_db,
        "connect",
        _connect(connection),
    )

    with pytest.raises(PermissionError, match="worker_availability_expired"):
        movement_match_safety.SafePostgresMovementStore().accept_match(
            proposal_id=PROPOSAL,
            worker_identity_id=WORKER,
        )
    assert connection.committed is False


def test_accept_rejects_role_revoked_after_proposal(monkeypatch):
    available_until = datetime.now(timezone.utc) + timedelta(minutes=15)
    connection = _Connection(
        [
            ("FROM oap_movement_match_proposals", (BOOKING, "driver", "PROPOSED")),
            ("FROM oap_movement_bookings", ("MATCH_PROPOSED",)),
            ("FROM oap_movement_availability", ("ONLINE", available_until)),
            ("FROM oap_identity_roles", None),
        ]
    )
    monkeypatch.setattr(
        movement_match_safety.postgres_db,
        "connect",
        _connect(connection),
    )

    with pytest.raises(PermissionError, match="certified_movement_role_required"):
        movement_match_safety.SafePostgresMovementStore().accept_match(
            proposal_id=PROPOSAL,
            worker_identity_id=WORKER,
        )
    assert connection.committed is False


def test_accept_locks_revalidates_expires_competing_proposals_and_marks_busy(monkeypatch):
    now = datetime.now(timezone.utc)
    available_until = now + timedelta(minutes=15)
    connection = _Connection(
        [
            ("FROM oap_movement_match_proposals", (BOOKING, "driver", "PROPOSED")),
            ("FROM oap_movement_bookings", ("MATCH_PROPOSED",)),
            ("FROM oap_movement_availability", ("ONLINE", available_until)),
            ("FROM oap_identity_roles", (1,)),
            ("WHERE booking_id=%s AND state='ACCEPTED'", None),
            ("SET state='ACCEPTED'", (BOOKING, "driver", now)),
            ("SET state='EXPIRED'", None),
            ("SET state='ACCEPTED',updated_at=CURRENT_TIMESTAMP", (BOOKING,)),
            ("SET availability_state='BUSY'", (WORKER,)),
        ]
    )
    monkeypatch.setattr(
        movement_match_safety.postgres_db,
        "connect",
        _connect(connection),
    )

    result = movement_match_safety.SafePostgresMovementStore().accept_match(
        proposal_id=PROPOSAL,
        worker_identity_id=WORKER,
    )

    assert result["state"] == "ACCEPTED"
    assert result["certification_revalidated"] is True
    assert result["availability_revalidated"] is True
    assert result["other_proposals_expired"] is True
    assert result["external_dispatch_performed"] is False
    assert connection.committed is True
    locking_reads = [query for query in connection.queries[:3] if "FOR UPDATE" in query]
    assert len(locking_reads) == 3
