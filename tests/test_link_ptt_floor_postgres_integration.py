"""Real isolated PostgreSQL proof of PTT floor contention, expiry and irrevocable STOP."""
from __future__ import annotations

import os
import uuid
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier

import pytest

from mission_control import link_call_audit, link_ptt_floor, postgres_db

pytestmark = pytest.mark.skipif(
    os.environ.get("OAP_REAL_POSTGRES_PROOF") != "1",
    reason="isolated real PostgreSQL proof is CI-gated",
)


def test_real_postgres_ptt_floor_contention_expiry_stop_and_call_isolation(monkeypatch):
    assert postgres_db.init_postgres(assume_yes=True)["initialized"] is True
    monkeypatch.setenv("OAP_LINK_CALL_AUDIT_RETENTION_DAYS", "7")
    link_call_audit.init_schema(assume_yes=True)
    link_call_audit.upgrade_ptt_mode(assume_yes=True)
    link_ptt_floor.init_schema(assume_yes=True)
    assert link_ptt_floor.status()["ready"] is True

    # These guards have independent unit tests; this proof targets real row locking.
    monkeypatch.setattr(link_call_audit, "_relationship_guard", lambda *_: None)
    monkeypatch.setattr(link_call_audit, "_youth_guard", lambda *_: None)

    first, second, outsider = (str(uuid.uuid4()) for _ in range(3))
    ptt_session, ordinary_session = (str(uuid.uuid4()) for _ in range(2))
    try:
        with postgres_db.connect() as connection:
            for identity in (first, second, outsider):
                connection.execute(
                    """INSERT INTO users(id,email,username,display_name,status)
                       VALUES (%s,%s,%s,%s,'active')""",
                    (identity, f"{identity}@example.invalid", f"ptt-{identity[:8]}", "PTT proof"),
                )
            for session, mode in ((ptt_session, "ptt"), (ordinary_session, "call")):
                connection.execute(
                    """INSERT INTO link_call_sessions(
                       session_id,initiator_id,recipient_id,mode,state,answered_at,expires_at)
                       VALUES (%s,%s,%s,%s,'active',CURRENT_TIMESTAMP,
                               CURRENT_TIMESTAMP + INTERVAL '1 hour')""",
                    (session, first, second, mode),
                )
            connection.commit()

        with pytest.raises(ValueError, match="active_ptt_call_required"):
            link_ptt_floor.floor(outsider, ptt_session, action="acquire")
        with pytest.raises(ValueError, match="active_ptt_call_required"):
            link_ptt_floor.floor(first, ordinary_session, action="acquire")

        together = Barrier(2)

        def acquire(identity):
            together.wait(timeout=5)
            try:
                return identity, link_ptt_floor.floor(identity, ptt_session, action="acquire")
            except ValueError as exc:
                return identity, str(exc)

        with ThreadPoolExecutor(max_workers=2) as executor:
            outcomes = list(executor.map(acquire, (first, second)))
        winners = [(identity, outcome) for identity, outcome in outcomes if isinstance(outcome, dict)]
        losers = [outcome for _, outcome in outcomes if isinstance(outcome, str)]
        assert len(winners) == 1
        assert losers == ["ptt_floor_busy"]
        winner = winners[0][0]
        loser = second if winner == first else first
        assert link_ptt_floor.read(first, ptt_session)["holder_id"] == winner

        # After the lease expires the other participant can take the floor.
        with postgres_db.connect() as connection:
            connection.execute(
                """UPDATE link_ptt_floor
                   SET lease_until=CURRENT_TIMESTAMP - INTERVAL '1 second'
                   WHERE session_id=%s""",
                (ptt_session,),
            )
            connection.commit()
        assert link_ptt_floor.floor(loser, ptt_session, action="acquire")["holder_id"] == loser
        assert link_ptt_floor.floor(winner, ptt_session, action="stop")["stopped"] is True

        # Late renew/release cannot reopen or delete the STOP tombstone.
        with pytest.raises(ValueError, match="ptt_floor_stopped"):
            link_ptt_floor.floor(loser, ptt_session, action="acquire")
        assert link_ptt_floor.floor(loser, ptt_session, action="release")["stopped"] is True
        assert link_ptt_floor.read(first, ptt_session) == {
            "holder_id": None, "stopped": True, "lease_seconds": 8,
        }
    finally:
        with postgres_db.connect() as connection:
            connection.execute(
                "DELETE FROM link_call_sessions WHERE session_id IN (%s,%s)",
                (ptt_session, ordinary_session),
            )
            connection.execute(
                "DELETE FROM users WHERE id IN (%s,%s,%s)",
                (first, second, outsider),
            )
            connection.commit()
