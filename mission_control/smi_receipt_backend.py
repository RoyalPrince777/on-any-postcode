"""Founder-only HRM/SMI receipt backend with durable Postgres preference.

The backend prefers an independent HRM Postgres database when configured and
falls back to local SQLite without pretending that the fallback is durable.
It records proof metadata only and grants no execution or approval authority.
"""
from __future__ import annotations

import base64
import hashlib
import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

DEFAULT_DB_PATH = "/tmp/oap_smi_receipts.sqlite3"
ALLOWED_RECEIPT_KINDS = {
    "hrm_neon_evidence_receipt",
    "matrix_learning_receipt",
    "war_room_live_proof_receipt",
    "agent_tool_connection_receipt",
    "ecosystem_outcome_receipt",
    "behaviour_response_receipt",
    "behaviour_score_receipt",
    "behaviour_learning_receipt",
    "behaviour_step4_readiness_receipt",
    "studio_generation_receipt",
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _db_path() -> str:
    configured = os.getenv("OAP_SMI_RECEIPT_DB_PATH") or os.getenv("OAP_RECEIPT_DB_PATH")
    return configured or DEFAULT_DB_PATH


def _decode_b64(value: str) -> str:
    try:
        return base64.b64decode(value.encode("ascii"), validate=True).decode("utf-8").strip()
    except (ValueError, UnicodeError):
        return ""


def _hrm_database_url() -> str:
    direct = (
        os.getenv("OAP_HRM_DATABASE_URL")
        or os.getenv("OAP_SMI_HRM_DATABASE_URL")
        or ""
    ).strip()
    if direct:
        return direct
    encoded = (
        os.getenv("OAP_HRM_DATABASE_URL_B64")
        or os.getenv("OAP_SMI_HRM_DATABASE_URL_B64")
        or ""
    ).strip()
    return _decode_b64(encoded) if encoded else ""


def _ssl_database_url(url: str) -> str:
    clean = str(url or "").strip()
    if not clean or "sslmode=" in clean:
        return clean
    if clean.startswith(("postgres://", "postgresql://")):
        return clean + ("&sslmode=require" if "?" in clean else "?sslmode=require")
    return clean


def _connect_sqlite() -> sqlite3.Connection:
    db_path = _db_path()
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def _init_sqlite_schema(connection: sqlite3.Connection) -> None:
    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS smi_evidence_receipts (
            receipt_id TEXT PRIMARY KEY,
            receipt_kind TEXT NOT NULL,
            brain_part TEXT NOT NULL,
            gate INTEGER NOT NULL,
            command TEXT NOT NULL,
            signal TEXT NOT NULL,
            guardian TEXT NOT NULL,
            green_gate TEXT NOT NULL,
            founder_final TEXT NOT NULL,
            payload_json TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_smi_receipts_part_gate ON smi_evidence_receipts(brain_part, gate)"
    )
    connection.execute(
        "CREATE INDEX IF NOT EXISTS idx_smi_receipts_kind ON smi_evidence_receipts(receipt_kind)"
    )
    connection.commit()


def _connect_postgres():
    import psycopg
    from psycopg.rows import dict_row

    url = _ssl_database_url(_hrm_database_url())
    if not url:
        raise RuntimeError("hrm_database_url_not_configured")
    return psycopg.connect(url, row_factory=dict_row)


def _init_postgres_schema(connection) -> None:
    with connection.cursor() as cursor:
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS smi_evidence_receipts (
                receipt_id TEXT PRIMARY KEY,
                receipt_kind TEXT NOT NULL,
                brain_part TEXT NOT NULL,
                gate INTEGER NOT NULL,
                command TEXT NOT NULL,
                signal TEXT NOT NULL,
                guardian TEXT NOT NULL,
                green_gate TEXT NOT NULL,
                founder_final TEXT NOT NULL,
                payload_json JSONB NOT NULL,
                created_at TIMESTAMPTZ NOT NULL
            )
            """
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_smi_receipts_part_gate ON smi_evidence_receipts(brain_part, gate)"
        )
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_smi_receipts_kind ON smi_evidence_receipts(receipt_kind)"
        )
    connection.commit()


def _normalise_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "brain_part": str(payload.get("brain_part") or "unknown"),
        "gate": int(payload.get("gate") or 0),
        "command": str(payload.get("command") or "war_room"),
        "signal": str(payload.get("signal") or "🟢"),
        "guardian": str(payload.get("guardian") or "required"),
        "green_gate": str(payload.get("green_gate") or "required"),
        "founder_final": str(payload.get("founder_final") or "required_for_full_green"),
        "safe_payload": dict(payload.get("safe_payload") or {}),
    }


def _base_result(kind: str, normalised: dict[str, Any], receipt_id: str, created_at: str) -> dict[str, Any]:
    return {
        "receipt_kind": kind,
        "receipt_id": receipt_id,
        "brain_part": normalised["brain_part"],
        "gate": normalised["gate"],
        "command": normalised["command"],
        "created_at": created_at,
        "neon_mirror": "not_required_for_independent_hrm_durability",
    }


def _write_postgres(kind: str, normalised: dict[str, Any], receipt_id: str, created_at: str, *, independent_readback: bool = False) -> dict[str, Any]:
    with _connect_postgres() as connection:
        if not independent_readback:
            # Normal receipts keep their existing initialization behavior.
            # A Recovery proof may write only to a previously prepared schema:
            # it must not CREATE TABLE / INDEX as a diagnostic side effect.
            _init_postgres_schema(connection)
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO smi_evidence_receipts (
                    receipt_id, receipt_kind, brain_part, gate, command, signal,
                    guardian, green_gate, founder_final, payload_json, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::timestamptz)
                """,
                (
                    receipt_id,
                    kind,
                    normalised["brain_part"],
                    normalised["gate"],
                    normalised["command"],
                    normalised["signal"],
                    normalised["guardian"],
                    normalised["green_gate"],
                    normalised["founder_final"],
                    json.dumps(normalised["safe_payload"], sort_keys=True),
                    created_at,
                ),
            )
        connection.commit()
        if not independent_readback:
            # Preserve the existing ordinary receipt flow. Recovery certification
            # requires the stronger separate-connection readback below.
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT receipt_id, receipt_kind FROM smi_evidence_receipts WHERE receipt_id = %s",
                    (receipt_id,),
                )
                row = cursor.fetchone()
    if independent_readback:
        # A new connection after the writer closed must see the committed row.
        # No schema initialization, second insert, or ephemeral fallback here.
        with _connect_postgres() as reader, reader.cursor() as cursor:
            cursor.execute("SET TRANSACTION READ ONLY")
            cursor.execute(
                "SELECT receipt_id, receipt_kind, payload_json FROM smi_evidence_receipts WHERE receipt_id = %s",
                (receipt_id,),
            )
            row = cursor.fetchone()
    read_back_ok = bool(row and row["receipt_id"] == receipt_id and row["receipt_kind"] == kind)
    if independent_readback:
        # Matching an ID and kind alone cannot detect a wrong/truncated payload.
        # JSONB is semantic data, so normalize its object rather than its
        # incidental textual serialization or key order.
        stored_payload = row.get("payload_json") if row else None
        if isinstance(stored_payload, str):
            stored_payload = json.loads(stored_payload)
        read_back_ok = bool(read_back_ok and stored_payload == normalised["safe_payload"])
    read_back_checksum_sha256 = (
        hashlib.sha256(
            json.dumps(
                {
                    "receipt_id": receipt_id,
                    "receipt_kind": kind,
                    "safe_payload": normalised["safe_payload"],
                },
                sort_keys=True,
                separators=(",", ":"),
                ensure_ascii=False,
            ).encode("utf-8")
        ).hexdigest()
        if independent_readback and read_back_ok
        else None
    )
    return {
        **_base_result(kind, normalised, receipt_id, created_at),
        "read_back_checksum_sha256": read_back_checksum_sha256,
        "ok": read_back_ok,
        "status": "written_and_read_back" if read_back_ok else "write_failed_or_unreadable",
        "read_back_ok": read_back_ok,
        "backend": "independent_hrm_postgres",
        "durable": read_back_ok,
        "fallback_used": False,
    }


def _write_sqlite(kind: str, normalised: dict[str, Any], receipt_id: str, created_at: str, *, fallback_used: bool) -> dict[str, Any]:
    with _connect_sqlite() as connection:
        _init_sqlite_schema(connection)
        connection.execute(
            """
            INSERT INTO smi_evidence_receipts (
                receipt_id, receipt_kind, brain_part, gate, command, signal,
                guardian, green_gate, founder_final, payload_json, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                receipt_id,
                kind,
                normalised["brain_part"],
                normalised["gate"],
                normalised["command"],
                normalised["signal"],
                normalised["guardian"],
                normalised["green_gate"],
                normalised["founder_final"],
                json.dumps(normalised["safe_payload"], sort_keys=True),
                created_at,
            ),
        )
        connection.commit()
        row = connection.execute(
            "SELECT receipt_id, receipt_kind FROM smi_evidence_receipts WHERE receipt_id = ?",
            (receipt_id,),
        ).fetchone()
    read_back_ok = bool(row and row["receipt_id"] == receipt_id and row["receipt_kind"] == kind)
    return {
        **_base_result(kind, normalised, receipt_id, created_at),
        "ok": read_back_ok,
        "status": "written_and_read_back" if read_back_ok else "write_failed_or_unreadable",
        "read_back_ok": read_back_ok,
        "backend": "local_sqlite_receipt_store",
        "durable": False,
        "fallback_used": fallback_used,
    }


def write_receipt(receipt_kind: str, payload: dict[str, Any], *, require_durable: bool = False) -> dict[str, Any]:
    """Write one bounded receipt; prefer independent durable Postgres."""

    kind = str(receipt_kind or "").strip()
    if kind not in ALLOWED_RECEIPT_KINDS:
        return {
            "ok": False,
            "status": "blocked_unknown_receipt_kind",
            "receipt_kind": kind,
            "receipt_id": None,
            "read_back_ok": False,
            "durable": False,
        }

    normalised = _normalise_payload(payload)
    receipt_id = f"smi-{uuid.uuid4().hex}"
    created_at = _now()
    if _hrm_database_url():
        try:
            if require_durable:
                return _write_postgres(
                    kind, normalised, receipt_id, created_at, independent_readback=True
                )
            return _write_postgres(kind, normalised, receipt_id, created_at)
        except Exception:  # noqa: BLE001 - no secret or driver error in proof response
            if require_durable:
                # A failed readback may follow a successful commit. Retain the
                # correlation ID for later reconciliation and DO NOT write a
                # misleading second proof into ephemeral SQLite.
                return {
                    "ok": False,
                    "status": "durable_commit_or_readback_unconfirmed",
                    "receipt_kind": kind,
                    "receipt_id": receipt_id,
                    "read_back_ok": False,
                    "durable": False,
                    "backend": "independent_hrm_postgres",
                    "fallback_used": False,
                }
            result = _write_sqlite(kind, normalised, receipt_id, created_at, fallback_used=True)
            result["primary_backend_error"] = "independent_hrm_postgres_unavailable"
            return result
    if require_durable:
        return {
            "ok": False,
            "status": "blocked_durable_hrm_unconfigured",
            "receipt_kind": kind,
            "receipt_id": None,
            "read_back_ok": False,
            "durable": False,
            "backend": "unconfigured",
            "fallback_used": False,
        }
    return _write_sqlite(kind, normalised, receipt_id, created_at, fallback_used=False)



def verify_matrix_review_outcome(
    receipt_id: str, *, proposal_id: str, signal_id: str
) -> dict[str, Any]:
    """Read one independent HRM review row; never infer approval from a supplied ID.

    This checks stored evidence identity and declared review fields, not the
    independent reasoning ability of any specialist or external execution.
    """
    reference = str(receipt_id or "").strip()
    proposal = str(proposal_id or "").strip()
    signal = str(signal_id or "").strip()
    result: dict[str, Any] = {
        "verified": False,
        "receipt_id": reference,
        "source": "independent_hrm_postgres",
        "status": "review_unverified",
        "authority_granted": False,
        "actual_votes_proven": False,
    }
    if not reference or not proposal or not signal or not _hrm_database_url():
        return result
    try:
        with _connect_postgres() as connection, connection.cursor() as cursor:
            cursor.execute("SET TRANSACTION READ ONLY")
            cursor.execute(
                """SELECT receipt_id, receipt_kind, brain_part, command, payload_json
                   FROM smi_evidence_receipts WHERE receipt_id = %s""",
                (reference,),
            )
            row = cursor.fetchone()
    except Exception:  # noqa: BLE001 - no storage details in proof response
        return result
    if not row or row["receipt_id"] != reference:
        return result
    payload = row.get("payload_json")
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except ValueError:
            return result
    if not isinstance(payload, dict):
        return result
    valid = (
        row["receipt_kind"] == "war_room_live_proof_receipt"
        and row["brain_part"] == "matrix"
        and row["command"] == "matrix_review_outcome"
        and payload.get("proposal_id") == proposal
        and payload.get("signal_id") == signal
        and payload.get("review_mode") == "first_party_matrix_review"
        and payload.get("evidence_verified") is True
        and payload.get("reviewed") is True
        and payload.get("founder_approved") is True
        and payload.get("guardian_pass") is True
        and payload.get("green_gate_pass") is True
        and payload.get("execution_granted") is False
    )
    if valid:
        result["verified"] = True
        result["status"] = "stored_review_fields_matched"
    return result


def _latest_postgres(limit: int) -> tuple[dict[str, Any], ...]:
    with _connect_postgres() as connection, connection.cursor() as cursor:
        cursor.execute("SET TRANSACTION READ ONLY")
        cursor.execute(
            """
            SELECT receipt_id, receipt_kind, brain_part, gate, command, signal,
                   guardian, green_gate, founder_final, created_at
            FROM smi_evidence_receipts
            ORDER BY created_at DESC
            LIMIT %s
            """,
            (limit,),
        )
        rows = cursor.fetchall()
    return tuple(dict(row) for row in rows)


def _latest_sqlite(limit: int) -> tuple[dict[str, Any], ...]:
    # SQLite's normal connector and schema initializer create files/tables.
    # Status reads must never create either on a missing fallback store.
    with sqlite3.connect(Path(_db_path()).resolve().as_uri() + "?mode=ro", uri=True) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            """
            SELECT receipt_id, receipt_kind, brain_part, gate, command, signal,
                   guardian, green_gate, founder_final, created_at
            FROM smi_evidence_receipts
            ORDER BY created_at DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return tuple(dict(row) for row in rows)


def latest_receipts(limit: int = 20) -> dict[str, Any]:
    """Return recent receipt metadata without private payloads."""

    safe_limit = max(1, min(int(limit or 20), 100))
    backend = "local_sqlite_receipt_store"
    durable = False
    fallback_used = False
    if _hrm_database_url():
        try:
            rows = _latest_postgres(safe_limit)
            backend = "independent_hrm_postgres"
            durable = True
        except Exception:  # noqa: BLE001
            fallback_used = True
            try:
                rows = _latest_sqlite(safe_limit)
            except (sqlite3.Error, OSError):
                rows = ()
    else:
        try:
            rows = _latest_sqlite(safe_limit)
        except (sqlite3.Error, OSError):
            rows = ()
    return {
        "name": "SMI Evidence Receipts",
        "backend": backend,
        "durable": durable,
        "fallback_used": fallback_used,
        "count": len(rows),
        "receipts": rows,
        "neon_mirror": "optional_not_authoritative",
    }



def behaviour_progress(limit: int = 20) -> dict[str, Any]:
    """Return Founder-safe Behaviour protocol receipt progress and score trends."""
    safe_limit = max(1, min(int(limit or 20), 100))
    kinds = (
        "behaviour_response_receipt",
        "behaviour_score_receipt",
        "behaviour_learning_receipt",
        "behaviour_step4_readiness_receipt",
    )
    rows: list[dict[str, Any]] = []
    if _hrm_database_url():
        try:
            with _connect_postgres() as connection:
                _init_postgres_schema(connection)
                with connection.cursor() as cursor:
                    cursor.execute(
                        """
                        SELECT receipt_kind, gate, command, green_gate, founder_final,
                               payload_json, created_at
                        FROM smi_evidence_receipts
                        WHERE receipt_kind = ANY(%s)
                        ORDER BY created_at DESC
                        LIMIT %s
                        """,
                        (list(kinds), safe_limit),
                    )
                    rows = [dict(row) for row in cursor.fetchall()]
        except Exception:  # noqa: BLE001
            rows = []

    present = {str(row.get("receipt_kind")) for row in rows}
    score_trend = []
    for row in rows:
        if row.get("receipt_kind") != "behaviour_score_receipt":
            continue
        payload = row.get("payload_json") or {}
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except json.JSONDecodeError:
                payload = {}
        score_trend.append(
            {
                "created_at": row.get("created_at"),
                "coverage_percentage": payload.get("coverage_percentage"),
                "measured_average_percentage": payload.get(
                    "measured_average_percentage"
                ),
                "overall_percentage": payload.get("overall_percentage"),
                "overall_evidence_state": payload.get("overall_evidence_state"),
            }
        )

    proven = 0
    if "behaviour_response_receipt" in present:
        proven = 25
    if "behaviour_score_receipt" in present:
        proven = 50
    if "behaviour_learning_receipt" in present:
        proven = 75
    step4_ready = "behaviour_step4_readiness_receipt" in present
    return {
        "protocol": "Behaviour Intelligence 4-step / 25% protocol",
        "proven_percentage": proven,
        "step4_readiness_receipt": step4_ready,
        "full_green": False,
        "founder_final": "waiting",
        "green_gate": "required",
        "score_trend": tuple(score_trend),
        "receipt_kinds_present": tuple(sorted(present)),
        "human_authority_final": True,
    }


def _configured_hrm_host_fingerprint() -> str | None:
    """Fingerprint only the actual receipt-writer host; never return its URL."""

    try:
        hostname = (urlsplit(_hrm_database_url()).hostname or "").lower().rstrip(".")
    except ValueError:
        return None
    if not hostname:
        return None
    return hashlib.sha256(hostname.encode("utf-8")).hexdigest()


def _configured_main_host_fingerprint() -> str | None:
    """Fingerprint the selected main writer host, not the unused primary URL."""

    from . import postgres_db

    try:
        hostname = (urlsplit(postgres_db._database_url()).hostname or "").lower().rstrip(".")
    except ValueError:
        return None
    if not hostname:
        return None
    return hashlib.sha256(hostname.encode("utf-8")).hexdigest()


def backend_configuration_status() -> dict[str, Any]:
    """Return configuration state without making a DB connection or leaking secrets."""

    from . import postgres_db

    durable_configured = bool(_hrm_database_url())
    return {
        "durable_backend_configured": durable_configured,
        "hrm_host_sha256": _configured_hrm_host_fingerprint(),
        "main_host_sha256": _configured_main_host_fingerprint(),
        "main_database_source": postgres_db.database_source(),
        "main_database_authority": postgres_db.database_authority(),
        "live_store_identity_proven": False,
        "preferred_backend": "independent_hrm_postgres" if durable_configured else "local_sqlite_receipt_store",
        "fallback_backend": "local_sqlite_receipt_store",
        "fallback_is_durable": False,
        "neon_required": False,
        "secret_values_exposed": False,
    }


def receipt_backend_status(*, require_durable: bool = False) -> dict[str, Any]:
    """Prove write/read readiness; Recovery POST must never use SQLite."""

    probe_payload = {
        "brain_part": "receipt_backend_probe",
        "gate": 5,
        "command": "backend_status",
        "signal": "🟢",
        "safe_payload": {"probe": True, "external_action": False},
    }
    if require_durable:
        # A probe has not passed the whole recovery gate even if this receipt
        # later commits. Never write a pre-certified green signal.
        probe_payload["signal"] = "🟣"
        probe = write_receipt(
            "hrm_neon_evidence_receipt", probe_payload, require_durable=True
        )
    else:
        probe = write_receipt("hrm_neon_evidence_receipt", probe_payload)
    durable_ready = bool(
        probe.get("ok")
        and probe.get("read_back_ok")
        and probe.get("durable")
        and not probe.get("fallback_used")
        and probe.get("backend") == "independent_hrm_postgres"
    )
    return {
        "name": "SMI Receipt Backend Status",
        "receipt_backend": probe["backend"],
        "write_read_proof": probe,
        "hrm_receipt_ready": durable_ready,
        "matrix_learning_receipt_ready": durable_ready,
        "ecosystem_outcome_receipt_ready": durable_ready,
        "independent_durable_hrm_ready": durable_ready,
        "neon_mirror_ready": False,
        "neon_mirror_reason": "Neon is optional as a mirror; independent HRM durability is authoritative when configured and proven.",
        "full_system_green": False,
        "locks": {
            "founder_only": True,
            "no_fake_green": True,
            "no_external_execution": True,
            "no_self_approval": True,
            "public_private_separation": True,
        },
    }
