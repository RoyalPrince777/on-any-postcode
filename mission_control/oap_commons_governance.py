"""OAP Commons private lifecycle, reusing the existing workspace/audit ledger.

This code issues no government powers, public votes, publication or legal orders.
The immutable audit chain retains a minimal pseudonymous receipt after withdrawal.
90-day content retention requires a Founder-invoked bounded erasure sweep.
"""
from __future__ import annotations

import hashlib
import json
import uuid

from . import oap_commons, postgres_db

REVIEW_OUTCOMES = frozenset({"NOTED", "FURTHER_REVIEW", "OUT_OF_SCOPE"})
REDACTED_CONTENT = json.dumps({
    "state": "REDACTED", "title": "", "body": "",
    "consent_to_private_review": False, "published": False,
}, separators=(",", ":"))


def _uuid(raw: object) -> str:
    try:
        return str(uuid.UUID(str(raw)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError("invalid_commons_identity_or_proposal") from exc


def _receipt(db, *, actor: str, action: str, proposal_id: str,
             metadata: dict[str, object]) -> None:
    # All callers hold the same global audit-chain transaction lock used by
    # the existing OAP workspace/audit writes. No network call or mock ledger.
    previous = db.execute(
        "SELECT curr_hash FROM audit_events ORDER BY event_seq DESC LIMIT 1"
    ).fetchone()
    previous_hash = str(previous[0]) if previous else "GENESIS"
    canonical = json.dumps(metadata, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256((previous_hash + canonical).encode("utf-8")).hexdigest()
    db.execute(
        """INSERT INTO audit_events(
           prev_hash,curr_hash,actor_id,actor_type,authority_level,
           action,target,reason,correlation_id,metadata
           ) VALUES (%s,%s,%s,'USER',5,%s,%s,%s,%s,%s::jsonb)""",
        (previous_hash, digest, actor, action, f"oap_commons:{proposal_id}",
         "oap_commons_member_rights_and_review", proposal_id, canonical),
    )


def withdraw(member_id: object, proposal_id: object) -> dict[str, object]:
    """Revoke consent to private review; immediately redact stored text."""
    owner, pid = _uuid(member_id), _uuid(proposal_id)
    try:
        with postgres_db.connect() as db:
            db.execute("SELECT pg_advisory_xact_lock(%s)", (24680259,))
            row = db.execute(
                """SELECT record_id FROM oap_workspace_records
                   WHERE identity_id=%s AND workspace_id='governance'
                     AND title=%s AND status='draft' FOR UPDATE""",
                (owner, oap_commons.PREFIX + pid),
            ).fetchone()
            if row is None:
                raise ValueError("commons_proposal_not_found")
            db.execute(
                """UPDATE oap_workspace_records
                   SET body=%s,status='archived',updated_at=CURRENT_TIMESTAMP
                   WHERE record_id=%s""",
                (REDACTED_CONTENT, str(row[0])),
            )
            _receipt(
                db, actor=owner, action="OAP_COMMONS_CONSENT_WITHDRAWN",
                proposal_id=pid,
                metadata={"proposal_id": pid, "content_redacted": True,
                          "consent": False, "published": False},
            )
            db.commit()
    except ValueError:
        raise
    except Exception as exc:
        raise oap_commons.CommonsUnavailable("commons_withdrawal_unavailable") from exc
    return {
        "proposal_id": pid, "state": "WITHDRAWN",
        "content_redacted": True, "audit_linkage_retained": True,
        "published": False,
    }


def review(founder_id: object, proposal_id: object, *,
           outcome: object, reason: object) -> dict[str, object]:
    """Record a nonbinding human reply; does not approve, publish or vote."""
    actor, pid = _uuid(founder_id), _uuid(proposal_id)
    if not isinstance(outcome, str) or outcome not in REVIEW_OUTCOMES:
        raise ValueError("invalid_commons_outcome")
    note = oap_commons._clean_text(reason, min_length=10, max_length=500)
    try:
        with postgres_db.connect() as db:
            db.execute("SELECT pg_advisory_xact_lock(%s)", (24680259,))
            row = db.execute(
                """SELECT record_id,body FROM oap_workspace_records
                   WHERE workspace_id='governance' AND title=%s
                     AND status='draft'
                     AND created_at >= CURRENT_TIMESTAMP - INTERVAL '90 days'
                   FOR UPDATE""",
                (oap_commons.PREFIX + pid,),
            ).fetchone()
            if row is None:
                raise ValueError("commons_review_not_available")
            try:
                stored = json.loads(str(row[1]))
            except (TypeError, ValueError) as exc:
                raise oap_commons.CommonsUnavailable("commons_review_corrupt") from exc
            if (not isinstance(stored, dict)
                or stored.get("state") != "PENDING_FOUNDER_REVIEW"
                or stored.get("consent_to_private_review") is not True
                or stored.get("published") is not False):
                raise ValueError("commons_review_not_available")
            stored.update({
                "state": "REVIEWED",
                "review_outcome": outcome,
                "review_note": note,
                "published": False,
            })
            db.execute(
                """UPDATE oap_workspace_records
                   SET body=%s,updated_at=CURRENT_TIMESTAMP WHERE record_id=%s""",
                (json.dumps(stored, ensure_ascii=False, separators=(",", ":")),
                 str(row[0])),
            )
            _receipt(
                db, actor=actor, action="OAP_COMMONS_HUMAN_REVIEW",
                proposal_id=pid,
                metadata={"proposal_id": pid, "outcome": outcome,
                          "nonbinding": True, "published": False,
                          "human_note_stored_privately": True},
            )
            db.commit()
    except (ValueError, oap_commons.CommonsUnavailable):
        raise
    except Exception as exc:
        raise oap_commons.CommonsUnavailable("commons_review_unavailable") from exc
    return {
        "proposal_id": pid, "state": "REVIEWED", "outcome": outcome,
        "published": False, "binding": False, "human_review": True,
    }


def erase_expired(founder_id: object, *, limit: int = 100) -> dict[str, object]:
    """Manually enforced 90-day erasure, with a minimal receipt per record."""
    actor = _uuid(founder_id)
    if type(limit) is not int or not 1 <= limit <= 100:
        raise ValueError("invalid_retention_limit")
    try:
        with postgres_db.connect() as db:
            db.execute("SELECT pg_advisory_xact_lock(%s)", (24680259,))
            rows = db.execute(
                """SELECT record_id,title FROM oap_workspace_records
                   WHERE workspace_id='governance' AND title LIKE %s
                     AND status='draft'
                     AND created_at < CURRENT_TIMESTAMP - INTERVAL '90 days'
                   ORDER BY created_at ASC LIMIT %s FOR UPDATE""",
                (oap_commons.PREFIX + "%", limit),
            ).fetchall()
            for record_id, title in rows:
                pid = _uuid(str(title)[len(oap_commons.PREFIX):])
                db.execute(
                    """UPDATE oap_workspace_records
                       SET body=%s,status='archived',updated_at=CURRENT_TIMESTAMP
                       WHERE record_id=%s""",
                    (REDACTED_CONTENT, str(record_id)),
                )
                _receipt(
                    db, actor=actor, action="OAP_COMMONS_RETENTION_REDACTED",
                    proposal_id=pid,
                    metadata={"proposal_id": pid, "content_redacted": True,
                              "retention_days": oap_commons.RETENTION_DAYS},
                )
            db.commit()
    except ValueError:
        raise
    except Exception as exc:
        raise oap_commons.CommonsUnavailable("commons_retention_unavailable") from exc
    return {
        "redacted_count": len(rows), "retention_days": oap_commons.RETENTION_DAYS,
        "automated_scheduler": False, "audit_linkage_retained": True,
    }
