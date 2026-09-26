"""Owner-scoped My World workspaces backed by Neon Postgres."""

from __future__ import annotations

import hashlib
import json
import uuid

from . import postgres_db

WORKSPACES: tuple[dict[str, str], ...] = (
    {"id": "ecosystem", "name": "Ecosystem", "icon": "🌍", "purpose": "Products, systems and connections."},
    {"id": "signals", "name": "Signals", "icon": "📡", "purpose": "Saved announcements and local observations."},
    {"id": "hrm-memory", "name": "HRM & Memory", "icon": "🧠", "purpose": "Private lessons, reviews and continuity notes."},
    {"id": "governance", "name": "Governance", "icon": "🛡️", "purpose": "Policies, decisions and protected review notes."},
    {"id": "performance", "name": "Performance", "icon": "📈", "purpose": "Clarity, stability, pace and outcomes."},
    {"id": "news", "name": "News", "icon": "📰", "purpose": "Local stories and verified information leads."},
    {"id": "transport", "name": "Transport", "icon": "🚚", "purpose": "Movement, bookings and route notes."},
    {"id": "market", "name": "Market", "icon": "🛍️", "purpose": "Listings, merchants and commerce planning."},
    {"id": "maps", "name": "Maps", "icon": "🗺️", "purpose": "Saved places, routes and location intelligence."},
    {"id": "identity", "name": "Identity", "icon": "👤", "purpose": "Your postcode identity and profile work."},
    {"id": "tv", "name": "OAP TV", "icon": "📺", "purpose": "Media, culture and creator planning."},
    {"id": "sika", "name": "SIKA", "icon": "💎", "purpose": "Contribution and trust-value records; not money."},
)
WORKSPACE_BY_ID = {item["id"]: item for item in WORKSPACES}


class WorkspaceUnavailable(RuntimeError):
    """Raised when owner-scoped workspace persistence fails safely."""


def get(workspace_id: object) -> dict[str, str] | None:
    return WORKSPACE_BY_ID.get(str(workspace_id or "").strip().casefold())


def _identity(value: object) -> str:
    try:
        return str(uuid.UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError("invalid_workspace_identity") from exc


def list_records(
    identity_id: object, workspace_id: object, *, limit: int = 50
) -> list[dict[str, str]]:
    identity = _identity(identity_id)
    workspace = get(workspace_id)
    if workspace is None:
        raise ValueError("invalid_workspace")
    try:
        with postgres_db.connect(readonly=True) as connection:
            rows = connection.execute(
                """SELECT record_id,title,body,status,created_at,updated_at
                   FROM oap_workspace_records
                   WHERE identity_id=%s AND workspace_id=%s
                     AND status <> 'archived'
                   ORDER BY updated_at DESC LIMIT %s""",
                (identity, workspace["id"], min(100, max(1, int(limit)))),
            ).fetchall()
    except Exception as exc:
        raise WorkspaceUnavailable("workspace_read_failed") from exc
    return [
        {
            "record_id": str(row[0]),
            "title": str(row[1]),
            "body": str(row[2]),
            "status": str(row[3]),
            "created_at": row[4].isoformat(),
            "updated_at": row[5].isoformat(),
        }
        for row in rows
    ]



def list_records_with_title_prefix(
    identity_id: object, workspace_id: object, *, title_prefix: str,
    limit: int = 100,
) -> list[dict[str, str]]:
    """Owner-scoped title-prefix read without the unrelated workspace top-100.

    This is ordinary mutable workspace storage, not an immutable or
    independently anchored research ledger. Never hide an over-limit history.
    """
    identity = _identity(identity_id)
    workspace = get(workspace_id)
    if workspace is None:
        raise ValueError("invalid_workspace")
    if not isinstance(title_prefix, str) or not title_prefix.startswith("OAP-LAB:"):
        raise ValueError("invalid_lab_prefix")
    bounded = min(100, max(1, int(limit)))
    try:
        with postgres_db.lab_connect(readonly=True) as connection:
            rows = connection.execute(
                """SELECT record_id,title,body,status,created_at,updated_at
                   FROM oap_workspace_records
                   WHERE identity_id=%s AND workspace_id=%s
                     AND title LIKE %s
                   ORDER BY updated_at DESC LIMIT %s""",
                (identity, workspace["id"], title_prefix + "%", bounded),
            ).fetchall()
    except Exception as exc:
        raise WorkspaceUnavailable("workspace_read_failed") from exc
    return [
        {
            "record_id": str(row[0]), "title": str(row[1]),
            "body": str(row[2]), "status": str(row[3]),
            "created_at": row[4].isoformat(),
            "updated_at": row[5].isoformat(),
        }
        for row in rows
    ]




def list_lab_audit_receipts(
    identity_id: object, notebook_id: object, *, limit: int = 100,
) -> list[dict[str, object]]:
    """Read canonical LAB save receipts for one owner/notebook from audit_events."""
    identity = _identity(identity_id)
    notebook = str(uuid.UUID(str(notebook_id)))
    bounded = min(100, max(1, int(limit)))
    try:
        with postgres_db.lab_connect(readonly=True) as connection:
            rows = connection.execute(
                """SELECT event_seq,actor_id,target,metadata
                   FROM audit_events
                   WHERE actor_id=%s
                     AND action='OAP_LAB_NOTEBOOK_SAVE'
                     AND target=%s
                   ORDER BY event_seq ASC LIMIT %s""",
                (identity, f"oap_lab_notebook:{notebook}", bounded),
            ).fetchall()
    except Exception as exc:
        raise WorkspaceUnavailable("workspace_audit_read_failed") from exc
    receipts = []
    for row in rows:
        metadata = row[3]
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except ValueError as exc:
                raise WorkspaceUnavailable("workspace_audit_metadata_invalid") from exc
        if not isinstance(metadata, dict):
            raise WorkspaceUnavailable("workspace_audit_metadata_invalid")
        receipts.append({
            "event_seq": int(row[0]),
            "actor_id": str(row[1]),
            "target": str(row[2]),
            "metadata": metadata,
        })
    return receipts


def add_lab_record_atomic(
    identity_id: object,
    *,
    title: object,
    body: object,
    notebook_id: object,
    version: int,
    digest: str,
) -> str:
    """Write one LAB draft and canonical audit event in one transaction.

    Reuses existing oap_workspace_records and audit_events tables. This proves
    transactional coupling in software; it does not make workspace rows
    immutable or create an independent recovery store.
    """
    identity = _identity(identity_id)
    notebook = str(uuid.UUID(str(notebook_id)))
    title_value = str(title or "").strip()[:160]
    body_value = str(body or "").strip()[:5000]
    if not title_value or not body_value:
        raise ValueError("workspace_title_and_body_required")
    if type(version) is not int or version < 1:
        raise ValueError("invalid_lab_version")
    if (
        not isinstance(digest, str) or len(digest) != 64
        or any(char not in "0123456789abcdef" for char in digest)
    ):
        raise ValueError("invalid_lab_digest")
    metadata = {
        "workspace_id": "governance",
        "notebook_id": notebook,
        "version": version,
        "digest": digest,
        "record_status": "draft",
        "publication_authorised": False,
        "execution_authorised": False,
    }
    try:
        with postgres_db.lab_connect() as connection:
            connection.execute("SELECT pg_advisory_xact_lock(%s)", (24680260,))
            recent = connection.execute(
                """SELECT COUNT(*) FROM oap_workspace_records
                   WHERE identity_id=%s
                     AND created_at >= CURRENT_TIMESTAMP - INTERVAL '1 minute'""",
                (identity,),
            ).fetchone()
            if recent and int(recent[0]) >= 20:
                raise ValueError("workspace_rate_limit")
            row = connection.execute(
                """INSERT INTO oap_workspace_records(
                       identity_id,workspace_id,title,body,status
                   ) VALUES (%s,'governance',%s,%s,'draft')
                   RETURNING record_id""",
                (identity, title_value, body_value),
            ).fetchone()
            record_id = str(row[0])
            connection.execute("SELECT pg_advisory_xact_lock(%s)", (24680259,))
            previous = connection.execute(
                "SELECT curr_hash FROM audit_events ORDER BY event_seq DESC LIMIT 1"
            ).fetchone()
            previous_hash = str(previous[0]) if previous else "GENESIS"
            canonical = json.dumps(
                {**metadata, "record_id": record_id},
                sort_keys=True, separators=(",", ":"),
            )
            current_hash = hashlib.sha256(
                (previous_hash + canonical).encode("utf-8")
            ).hexdigest()
            connection.execute(
                """INSERT INTO audit_events(
                       prev_hash,curr_hash,actor_id,actor_type,authority_level,
                       action,target,reason,correlation_id,metadata
                   ) VALUES (
                       %s,%s,%s,'HUMAN_AUTHORITY',0,
                       'OAP_LAB_NOTEBOOK_SAVE',%s,
                       'owner_scoped_research_draft_save',%s,%s::jsonb
                   )""",
                (
                    previous_hash, current_hash, identity,
                    f"oap_lab_notebook:{notebook}", notebook, canonical,
                ),
            )
            connection.commit()
    except ValueError:
        raise
    except Exception as exc:
        raise WorkspaceUnavailable("workspace_atomic_audit_write_failed") from exc
    return record_id


def add_record(
    identity_id: object,
    workspace_id: object,
    *,
    title: object,
    body: object,
    status: object = "active",
) -> str:
    identity = _identity(identity_id)
    workspace = get(workspace_id)
    if workspace is None:
        raise ValueError("invalid_workspace")
    title_value = str(title or "").strip()[:160]
    body_value = str(body or "").strip()[:5000]
    status_value = str(status or "active").strip().casefold()
    if not title_value or not body_value:
        raise ValueError("workspace_title_and_body_required")
    if status_value not in {"draft", "active"}:
        raise ValueError("invalid_workspace_status")
    try:
        with postgres_db.connect() as connection:
            recent = connection.execute(
                """SELECT COUNT(*) FROM oap_workspace_records
                   WHERE identity_id=%s
                     AND created_at >= CURRENT_TIMESTAMP - INTERVAL '1 minute'""",
                (identity,),
            ).fetchone()
            if recent and int(recent[0]) >= 20:
                raise ValueError("workspace_rate_limit")
            row = connection.execute(
                """INSERT INTO oap_workspace_records(
                       identity_id,workspace_id,title,body,status
                   ) VALUES (%s,%s,%s,%s,%s) RETURNING record_id""",
                (identity, workspace["id"], title_value, body_value, status_value),
            ).fetchone()
            connection.commit()
    except ValueError:
        raise
    except Exception as exc:
        raise WorkspaceUnavailable("workspace_write_failed") from exc
    return str(row[0])


def list_organiser_schedule_records(
    identity_id: object, external_id: object, *, limit: int = 100,
) -> list[dict[str, str]]:
    """Read only one owner's append-only Organiser mirror history."""
    identity = _identity(identity_id)
    schedule_id = str(external_id or "")
    prefix = f"OAP-ORGANISER-SCHEDULE:{schedule_id}:"
    bounded = min(100, max(1, int(limit)))
    try:
        with postgres_db.lab_connect(readonly=True) as connection:
            rows = connection.execute(
                """SELECT record_id,title,body,status,created_at,updated_at
                   FROM oap_workspace_records
                   WHERE identity_id=%s AND workspace_id='governance'
                     AND title LIKE %s
                   ORDER BY updated_at DESC LIMIT %s""",
                (identity, prefix + "%", bounded),
            ).fetchall()
    except Exception as exc:
        raise WorkspaceUnavailable("organiser_schedule_read_failed") from exc
    return [
        {
            "record_id": str(row[0]), "title": str(row[1]),
            "body": str(row[2]), "status": str(row[3]),
            "created_at": row[4].isoformat(), "updated_at": row[5].isoformat(),
        }
        for row in rows
    ]


def list_organiser_schedule_audit_receipts(
    identity_id: object, external_id: object, *, limit: int = 100,
) -> list[dict[str, object]]:
    identity = _identity(identity_id)
    schedule_id = str(external_id or "")
    bounded = min(100, max(1, int(limit)))
    try:
        with postgres_db.lab_connect(readonly=True) as connection:
            rows = connection.execute(
                """SELECT event_seq,actor_id,target,metadata
                   FROM audit_events
                   WHERE actor_id=%s
                     AND action='OAP_ORGANISER_SCHEDULE_SYNC'
                     AND target=%s
                   ORDER BY event_seq ASC LIMIT %s""",
                (identity, f"smi_organiser_schedule:{schedule_id}", bounded),
            ).fetchall()
    except Exception as exc:
        raise WorkspaceUnavailable("organiser_schedule_audit_read_failed") from exc
    receipts = []
    for row in rows:
        metadata = row[3]
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except ValueError as exc:
                raise WorkspaceUnavailable("organiser_schedule_audit_invalid") from exc
        if not isinstance(metadata, dict):
            raise WorkspaceUnavailable("organiser_schedule_audit_invalid")
        receipts.append({
            "event_seq": int(row[0]), "actor_id": str(row[1]),
            "target": str(row[2]), "metadata": metadata,
        })
    return receipts


def add_organiser_schedule_record_atomic(
    identity_id: object,
    *,
    external_id: str,
    version: int,
    digest: str,
    title: str,
    body: str,
) -> str:
    """Append a minimised schedule mirror and audit receipt atomically."""
    identity = _identity(identity_id)
    if type(version) is not int or version < 1:
        raise ValueError("invalid_schedule_version")
    if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
        raise ValueError("invalid_schedule_digest")
    if title != f"OAP-ORGANISER-SCHEDULE:{external_id}:v{version}":
        raise ValueError("invalid_schedule_record_title")
    if not body or len(body) > 5000:
        raise ValueError("invalid_schedule_record_body")
    metadata = {
        "workspace_id": "governance", "external_id": external_id,
        "version": version, "digest": digest, "record_status": "draft",
        "prompt_persisted": False, "execution_authorised": False,
    }
    try:
        with postgres_db.lab_connect() as connection:
            connection.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", (external_id,))
            duplicate = connection.execute(
                """SELECT 1 FROM oap_workspace_records
                   WHERE identity_id=%s AND workspace_id='governance' AND title=%s
                   LIMIT 1""",
                (identity, title),
            ).fetchone()
            if duplicate:
                raise ValueError("schedule_version_already_exists")
            row = connection.execute(
                """INSERT INTO oap_workspace_records(
                       identity_id,workspace_id,title,body,status
                   ) VALUES (%s,'governance',%s,%s,'draft')
                   RETURNING record_id""",
                (identity, title, body),
            ).fetchone()
            record_id = str(row[0])
            connection.execute("SELECT pg_advisory_xact_lock(%s)", (24680259,))
            previous = connection.execute(
                "SELECT curr_hash FROM audit_events ORDER BY event_seq DESC LIMIT 1"
            ).fetchone()
            previous_hash = str(previous[0]) if previous else "GENESIS"
            canonical = json.dumps(
                {**metadata, "record_id": record_id},
                sort_keys=True, separators=(",", ":"),
            )
            current_hash = hashlib.sha256(
                (previous_hash + canonical).encode("utf-8")
            ).hexdigest()
            connection.execute(
                """INSERT INTO audit_events(
                       prev_hash,curr_hash,actor_id,actor_type,authority_level,
                       action,target,reason,correlation_id,metadata
                   ) VALUES (
                       %s,%s,%s,'HUMAN_AUTHORITY',0,
                       'OAP_ORGANISER_SCHEDULE_SYNC',%s,
                       'owner_scoped_minimised_schedule_mirror',%s,%s::jsonb
                   )""",
                (
                    previous_hash, current_hash, identity,
                    f"smi_organiser_schedule:{external_id}", external_id, canonical,
                ),
            )
            connection.commit()
    except ValueError:
        raise
    except Exception as exc:
        raise WorkspaceUnavailable("organiser_schedule_atomic_write_failed") from exc
    return record_id




def list_studio_orchestration_records(
    identity_id: object, mission_id: object, *, limit: int = 100,
) -> list[dict[str, str]]:
    """Read one owner's append-only Studio orchestration history."""
    identity = _identity(identity_id)
    mission = str(uuid.UUID(str(mission_id)))
    prefix = f"OAP-STUDIO-ORCH:{mission}:"
    bounded = min(100, max(1, int(limit)))
    try:
        with postgres_db.connect(readonly=True) as connection:
            rows = connection.execute(
                """SELECT record_id,title,body,status,created_at,updated_at
                   FROM oap_workspace_records
                   WHERE identity_id=%s AND workspace_id='governance'
                     AND title LIKE %s
                   ORDER BY updated_at ASC LIMIT %s""",
                (identity, prefix + "%", bounded),
            ).fetchall()
    except Exception as exc:
        raise WorkspaceUnavailable("studio_orchestration_read_failed") from exc
    return [
        {
            "record_id": str(row[0]), "title": str(row[1]),
            "body": str(row[2]), "status": str(row[3]),
            "created_at": row[4].isoformat(), "updated_at": row[5].isoformat(),
        }
        for row in rows
    ]


def add_studio_orchestration_record_atomic(
    identity_id: object,
    *,
    mission_id: str,
    version: int,
    digest: str,
    title: str,
    body: str,
) -> str:
    """Append one owner-scoped orchestration checkpoint plus audit receipt atomically."""
    identity = _identity(identity_id)
    mission = str(uuid.UUID(str(mission_id)))
    if type(version) is not int or version < 1:
        raise ValueError("invalid_orchestration_version")
    if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
        raise ValueError("invalid_orchestration_digest")
    expected_title = f"OAP-STUDIO-ORCH:{mission}:v{version}"
    if title != expected_title:
        raise ValueError("invalid_orchestration_record_title")
    if not body or len(body) > 5000:
        raise ValueError("invalid_orchestration_record_body")
    metadata = {
        "workspace_id": "governance", "mission_id": mission,
        "version": version, "digest": digest, "record_status": "draft",
        "execution_authorised": False,
    }
    try:
        with postgres_db.connect() as connection:
            connection.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", (mission,))
            duplicate = connection.execute(
                """SELECT 1 FROM oap_workspace_records
                   WHERE identity_id=%s AND workspace_id='governance' AND title=%s
                   LIMIT 1""",
                (identity, title),
            ).fetchone()
            if duplicate:
                raise ValueError("orchestration_version_already_exists")
            row = connection.execute(
                """INSERT INTO oap_workspace_records(
                       identity_id,workspace_id,title,body,status
                   ) VALUES (%s,'governance',%s,%s,'draft')
                   RETURNING record_id""",
                (identity, title, body),
            ).fetchone()
            record_id = str(row[0])
            connection.execute("SELECT pg_advisory_xact_lock(%s)", (97531024,))
            previous = connection.execute(
                "SELECT curr_hash FROM audit_events ORDER BY event_seq DESC LIMIT 1"
            ).fetchone()
            previous_hash = str(previous[0]) if previous else "GENESIS"
            canonical = json.dumps(
                {**metadata, "record_id": record_id},
                sort_keys=True, separators=(",", ":"),
            )
            current_hash = hashlib.sha256(
                (previous_hash + canonical).encode("utf-8")
            ).hexdigest()
            connection.execute(
                """INSERT INTO audit_events(
                       prev_hash,curr_hash,actor_id,actor_type,authority_level,
                       action,target,reason,correlation_id,metadata
                   ) VALUES (
                       %s,%s,%s,'HUMAN_AUTHORITY',0,
                       'OAP_STUDIO_ORCHESTRATION_CHECKPOINT',%s,
                       'owner_scoped_nonconsequential_orchestration_state',%s,%s::jsonb
                   )""",
                (
                    previous_hash, current_hash, identity,
                    f"studio_orchestration:{mission}", mission, canonical,
                ),
            )
            connection.commit()
    except ValueError:
        raise
    except Exception as exc:
        raise WorkspaceUnavailable("studio_orchestration_atomic_write_failed") from exc
    return record_id


def list_studio_build_preview_records(
    identity_id: object, preview_id: object, *, limit: int = 100,
) -> list[dict[str, str]]:
    """Read one owner's append-only Studio Build Preview history."""
    identity = _identity(identity_id)
    preview = str(uuid.UUID(str(preview_id)))
    prefix = f"OAP-BUILD-PREVIEW:{preview}:"
    bounded = min(100, max(1, int(limit)))
    try:
        with postgres_db.connect(readonly=True) as connection:
            rows = connection.execute(
                """SELECT record_id,title,body,status,created_at,updated_at
                   FROM oap_workspace_records
                   WHERE identity_id=%s AND workspace_id='governance'
                     AND title LIKE %s
                   ORDER BY updated_at ASC LIMIT %s""",
                (identity, prefix + "%", bounded),
            ).fetchall()
    except Exception as exc:
        raise WorkspaceUnavailable("studio_build_preview_read_failed") from exc
    return [
        {
            "record_id": str(row[0]), "title": str(row[1]),
            "body": str(row[2]), "status": str(row[3]),
            "created_at": row[4].isoformat(), "updated_at": row[5].isoformat(),
        }
        for row in rows
    ]


def add_studio_build_preview_record_atomic(
    identity_id: object,
    *,
    preview_id: str,
    version: int,
    digest: str,
    title: str,
    body: str,
) -> str:
    """Append one isolated Build Preview version and matching audit receipt."""
    identity = _identity(identity_id)
    preview = str(uuid.UUID(str(preview_id)))
    if type(version) is not int or version < 1:
        raise ValueError("invalid_build_preview_version")
    if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
        raise ValueError("invalid_build_preview_digest")
    expected_title = f"OAP-BUILD-PREVIEW:{preview}:v{version}"
    if title != expected_title:
        raise ValueError("invalid_build_preview_record_title")
    if not body or len(body.encode("utf-8")) > 250_000:
        raise ValueError("invalid_build_preview_record_body")
    metadata = {
        "workspace_id": "governance",
        "preview_id": preview,
        "version": version,
        "digest": digest,
        "record_status": "draft",
        "production_deploy_authorised": False,
        "server_side_execution_authorised": False,
    }
    try:
        with postgres_db.connect() as connection:
            connection.execute("SELECT pg_advisory_xact_lock(hashtext(%s))", (preview,))
            duplicate = connection.execute(
                """SELECT 1 FROM oap_workspace_records
                   WHERE identity_id=%s AND workspace_id='governance' AND title=%s
                   LIMIT 1""",
                (identity, title),
            ).fetchone()
            if duplicate:
                raise ValueError("build_preview_version_already_exists")
            row = connection.execute(
                """INSERT INTO oap_workspace_records(
                       identity_id,workspace_id,title,body,status
                   ) VALUES (%s,'governance',%s,%s,'draft')
                   RETURNING record_id""",
                (identity, title, body),
            ).fetchone()
            record_id = str(row[0])
            connection.execute("SELECT pg_advisory_xact_lock(%s)", (86420975,))
            previous = connection.execute(
                "SELECT curr_hash FROM audit_events ORDER BY event_seq DESC LIMIT 1"
            ).fetchone()
            previous_hash = str(previous[0]) if previous else "GENESIS"
            canonical = json.dumps(
                {**metadata, "record_id": record_id},
                sort_keys=True, separators=(",", ":"),
            )
            current_hash = hashlib.sha256(
                (previous_hash + canonical).encode("utf-8")
            ).hexdigest()
            connection.execute(
                """INSERT INTO audit_events(
                       prev_hash,curr_hash,actor_id,actor_type,authority_level,
                       action,target,reason,correlation_id,metadata
                   ) VALUES (
                       %s,%s,%s,'HUMAN_AUTHORITY',0,
                       'OAP_STUDIO_BUILD_PREVIEW_VERSION',%s,
                       'owner_scoped_browser_isolated_preview',%s,%s::jsonb
                   )""",
                (
                    previous_hash,
                    current_hash,
                    identity,
                    f"studio_build_preview:{preview}",
                    preview,
                    canonical,
                ),
            )
            connection.commit()
    except ValueError:
        raise
    except Exception as exc:
        raise WorkspaceUnavailable("studio_build_preview_atomic_write_failed") from exc
    return record_id

def lab_immutability_status() -> dict[str, object]:
    """Read-only proof that LAB workspace rows are DB-protected from mutation.

    Software hashes/audit receipts are not enough. Green requires the active
    database itself to deny UPDATE and DELETE for the application role or to
    expose an enabled trigger that rejects those mutations for LAB rows.
    """
    result: dict[str, object] = {
        "database_enforced": False,
        "update_denied": False,
        "delete_denied": False,
        "protective_trigger_present": False,
        "schema_changed": False,
        "error": None,
    }
    try:
        with postgres_db.lab_connect(readonly=True) as connection:
            privileges = connection.execute(
                """SELECT
                       has_table_privilege(current_user,'oap_workspace_records','UPDATE'),
                       has_table_privilege(current_user,'oap_workspace_records','DELETE')"""
            ).fetchone()
            update_allowed = bool(privileges and privileges[0])
            delete_allowed = bool(privileges and privileges[1])
            result["update_denied"] = not update_allowed
            result["delete_denied"] = not delete_allowed
            trigger = connection.execute(
                """SELECT 1
                   FROM pg_trigger t
                   JOIN pg_class c ON c.oid=t.tgrelid
                   JOIN pg_namespace n ON n.oid=c.relnamespace
                   JOIN pg_proc p ON p.oid=t.tgfoid
                   WHERE n.nspname='public'
                     AND c.relname='oap_workspace_records'
                     AND t.tgname='oap_lab_workspace_immutable'
                     AND p.proname='oap_lab_workspace_immutable_guard'
                     AND NOT t.tgisinternal
                     AND t.tgenabled <> 'D'
                     AND pg_get_triggerdef(t.oid) ILIKE '%UPDATE%'
                     AND pg_get_triggerdef(t.oid) ILIKE '%DELETE%'
                   LIMIT 1"""
            ).fetchone()
            result["protective_trigger_present"] = trigger is not None
    except Exception:  # noqa: BLE001 - readiness probe exposes no DB details
        result["error"] = "workspace_immutability_probe_failed"
    result["database_enforced"] = bool(
        (result["update_denied"] and result["delete_denied"])
        or result["protective_trigger_present"]
    )
    return result


def status() -> dict[str, object]:
    result: dict[str, object] = {
        "workspaces": len(WORKSPACES),
        "schema_ready": False,
        "records": 0,
        "ready": False,
        "error": None,
    }
    try:
        with postgres_db.connect(readonly=True) as connection:
            exists = connection.execute(
                """SELECT 1 FROM information_schema.tables
                   WHERE table_schema='public'
                     AND table_name='oap_workspace_records'"""
            ).fetchone()
            result["schema_ready"] = exists is not None
            if exists:
                result["records"] = int(
                    connection.execute(
                        "SELECT COUNT(*) FROM oap_workspace_records"
                    ).fetchone()[0]
                )
    except Exception:  # noqa: BLE001
        result["error"] = "workspace_store_unavailable"
    result["ready"] = bool(result["schema_ready"] and result["workspaces"] == 12)
    return result
