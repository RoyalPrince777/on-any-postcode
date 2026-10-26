"""OAP Commons: voluntary private member proposal intake, no elections or votes.

Reuses the existing OAP governance workspace and transactional hash-chain audit.
No new public forum, automated decisions, independent government, or agent IDs.
"""
from __future__ import annotations

import hashlib
import json
import uuid

from . import postgres_db

PREFIX = "OAP-COMMONS:v1:"
MAX_TITLE = 100
MAX_BODY = 1200
MAX_PER_MINUTE = 3
MAX_LIST = 50


class CommonsUnavailable(RuntimeError):
    """Fail closed when the canonical OAP proposal store cannot be used."""


def _identity(raw: object) -> str:
    try:
        return str(uuid.UUID(str(raw)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError("invalid_member_identity") from exc


def _clean_text(value: object, *, max_length: int, min_length: int) -> str:
    if not isinstance(value, str):
        raise ValueError("invalid_proposal_text")
    cleaned = " ".join(value.split())
    if not min_length <= len(cleaned) <= max_length:
        raise ValueError("invalid_proposal_text")
    if any(ord(c) < 32 for c in cleaned):
        raise ValueError("invalid_proposal_text")
    return cleaned


def validate_proposal(title: object, body: object, consent: object) -> dict[str, str]:
    """User must explicitly opt into storage for Founder-only review."""
    if consent is not True:
        raise ValueError("explicit_commons_consent_required")
    return {
        "title": _clean_text(title, min_length=5, max_length=MAX_TITLE),
        "body": _clean_text(body, min_length=20, max_length=MAX_BODY),
    }


def submit(identity_id: object, *, title: object, body: object, consent: object) -> dict[str, object]:
    identity = _identity(identity_id)
    proposal = validate_proposal(title, body, consent)
    proposal_id = str(uuid.uuid4())
    content_hash = hashlib.sha256(json.dumps(
        proposal, sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")).hexdigest()
    stored = json.dumps({
        **proposal,
        "consent_to_private_review": True,
        "state": "PENDING_FOUNDER_REVIEW",
        "published": False,
        "vote_count": None,
    }, ensure_ascii=False, separators=(",", ":"))
    metadata = {
        "proposal_id": proposal_id,
        "content_hash": content_hash,
        "purpose": "voluntary_private_founder_review",
        "published": False,
        "decision": None,
        "consent": True,
    }
    try:
        with postgres_db.connect() as db:
            # Single transaction: limit, owner write, and canonical audit.
            db.execute("SELECT pg_advisory_xact_lock(%s)", (24680259,))
            active = db.execute(
                """SELECT COUNT(*) FROM oap_workspace_records
                   WHERE identity_id=%s AND workspace_id='governance'
                     AND title LIKE %s
                     AND created_at > CURRENT_TIMESTAMP - INTERVAL '1 minute'""",
                (identity, PREFIX + "%"),
            ).fetchone()
            if active and int(active[0]) >= MAX_PER_MINUTE:
                raise ValueError("commons_submission_rate_limited")
            record = db.execute(
                """INSERT INTO oap_workspace_records(
                   identity_id,workspace_id,title,body,status
                   ) VALUES (%s,'governance',%s,%s,'draft')
                   RETURNING record_id""",
                (identity, PREFIX + proposal_id, stored),
            ).fetchone()
            if record is None:
                raise CommonsUnavailable("commons_write_not_confirmed")
            previous = db.execute(
                "SELECT curr_hash FROM audit_events ORDER BY event_seq DESC LIMIT 1"
            ).fetchone()
            prior_hash = str(previous[0]) if previous else "GENESIS"
            canonical = json.dumps(metadata, sort_keys=True, separators=(",", ":"))
            audit_hash = hashlib.sha256((prior_hash + canonical).encode("utf-8")).hexdigest()
            db.execute(
                """INSERT INTO audit_events(
                   prev_hash,curr_hash,actor_id,actor_type,authority_level,
                   action,target,reason,correlation_id,metadata
                   ) VALUES (
                   %s,%s,%s,'USER',5,'OAP_COMMONS_PROPOSAL_RECEIVED',%s,
                   'explicit_private_review_consent',%s,%s::jsonb
                   )""",
                (prior_hash, audit_hash, identity,
                 f"oap_commons:{proposal_id}", proposal_id, canonical),
            )
            db.commit()
    except ValueError:
        raise
    except CommonsUnavailable:
        raise
    except Exception as exc:
        raise CommonsUnavailable("commons_submission_not_persisted") from exc
    return {
        "proposal_id": proposal_id,
        "state": "PENDING_FOUNDER_REVIEW",
        "audit_receipt_expected": True,
        "published": False,
        "voting_enabled": False,
        "human_review_required": True,
    }


def _safe_record(row: object) -> dict[str, object] | None:
    try:
        record_id, title_marker, data, created_at = row
        title_marker = str(title_marker)
        if not title_marker.startswith(PREFIX):
            return None
        proposal_id = str(uuid.UUID(title_marker[len(PREFIX):]))
        obj = json.loads(str(data))
        if (not isinstance(obj, dict) or obj.get("consent_to_private_review") is not True
            or obj.get("published") is not False
            or obj.get("state") != "PENDING_FOUNDER_REVIEW"):
            return None
        title = _clean_text(obj.get("title"), min_length=5, max_length=MAX_TITLE)
        body = _clean_text(obj.get("body"), min_length=20, max_length=MAX_BODY)
        return {
            "record_id": str(record_id),
            "proposal_id": proposal_id,
            "title": title,
            "body": body,
            "state": "PENDING_FOUNDER_REVIEW",
            "published": False,
            "created_at": created_at.isoformat(),
        }
    except (TypeError, ValueError, AttributeError, json.JSONDecodeError):
        return None


def mine(identity_id: object, *, limit: int = MAX_LIST) -> tuple[dict[str, object], ...]:
    identity = _identity(identity_id)
    try:
        with postgres_db.connect(readonly=True) as db:
            rows = db.execute(
                """SELECT record_id,title,body,created_at
                   FROM oap_workspace_records
                   WHERE identity_id=%s AND workspace_id='governance'
                     AND title LIKE %s AND status='draft'
                   ORDER BY created_at DESC LIMIT %s""",
                (identity, PREFIX + "%", max(1, min(limit, MAX_LIST))),
            ).fetchall()
    except Exception as exc:
        raise CommonsUnavailable("commons_private_list_unavailable") from exc
    return tuple(item for row in rows if (item := _safe_record(row)) is not None)


def founder_queue(*, limit: int = MAX_LIST) -> tuple[dict[str, object], ...]:
    """Called ONLY by existing Founder-authenticated /mission blueprint."""
    try:
        with postgres_db.connect(readonly=True) as db:
            rows = db.execute(
                """SELECT record_id,title,body,created_at
                   FROM oap_workspace_records
                   WHERE workspace_id='governance' AND title LIKE %s
                     AND status='draft'
                   ORDER BY created_at DESC LIMIT %s""",
                (PREFIX + "%", max(1, min(limit, MAX_LIST))),
            ).fetchall()
    except Exception as exc:
        raise CommonsUnavailable("commons_founder_queue_unavailable") from exc
    return tuple(item for row in rows if (item := _safe_record(row)) is not None)


def status() -> dict[str, object]:
    """Readiness describes the schema, NOT proof of a real successful submission."""
    schema_ready = False
    try:
        with postgres_db.connect(readonly=True) as db:
            rows = db.execute(
                """SELECT table_name FROM information_schema.tables
                   WHERE table_schema='public'
                     AND table_name IN ('oap_workspace_records','audit_events','users')"""
            ).fetchall()
            schema_ready = {str(r[0]) for r in rows} == {
                "oap_workspace_records", "audit_events", "users"
            }
    except Exception:  # noqa: BLE001 - no optimistic live claim
        pass
    return {
        "module": "OAP Commons",
        "status": "private_proposal_intake" if schema_ready else "store_unavailable",
        "schema_ready": schema_ready,
        "first_party_persistence": True,
        "consent_required": True,
        "private_until_review": True,
        "public_proposals_enabled": False,
        "public_voting_enabled": False,
        "representative_elections_enabled": False,
        "automatic_decisions": False,
        "real_submission_proof": False,
        "production_vpi_percent": None,
        "founder_final_required": True,
    }
