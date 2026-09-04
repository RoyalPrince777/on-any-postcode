"""OAP Safe Signals v0.3 — verified, lawful, human-first world signals.

This module powers Weather, News Facts, Civic Voice and Mentorship boards from
postcode to planet. It does not create political authority, legal/financial
advice, binding votes, fake petitions, autonomous civic action or youth pressure.
Schema changes are explicit and never run at import/startup time.
"""
from __future__ import annotations

import hashlib
from datetime import UTC, datetime
from typing import Any
from urllib.parse import urlparse
from uuid import UUID

from . import postgres_db

SAFE_SIGNALS_REVISION = "2026-09-04-v0.3"
SAFE_SIGNALS_MIGRATION_VERSION = "0009_safe_signals_v03"
PUBLIC_PROMISE = (
    "OAP shares verified facts, official links, weather signals, community needs, "
    "and lawful civic education. OAP does not provide legal or financial advice, "
    "does not fake signatures, does not pressure people, and does not replace "
    "official services."
)

SIGNAL_KINDS = frozenset({"WEATHER", "NEWS", "COMMUNITY", "HUMANITARIAN", "SCIENCE"})
AREA_LEVELS = frozenset(
    {"POSTCODE", "BOROUGH", "CITY", "COUNTRY", "CONTINENT", "WORLD", "UNIVERSE"}
)
SOURCE_TYPES = frozenset({"OFFICIAL", "REPUTABLE", "LOCAL_WITNESS", "CHARITY", "UNKNOWN"})
VERIFICATION_STATES = frozenset({"VERIFIED", "DEVELOPING", "UNKNOWN", "CORRECTED"})
RISK_LEVELS = frozenset({"GREEN", "AMBER", "RED"})
SIGNAL_STATES = frozenset({"DRAFT", "ACTIVE", "ARCHIVED", "CORRECTED"})
CIVIC_STATES = frozenset({"RESEARCHING", "ACTIVE", "CLOSED", "REVIEWED"})
MENTOR_AUDIENCES = frozenset({"YOUTH", "ADULT", "BUSINESS", "COMMUNITY_CAPTAIN"})

SAFE_SIGNALS_SCHEMA_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_world_signals (
        signal_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        kind TEXT NOT NULL CHECK (kind IN ('WEATHER','NEWS','COMMUNITY','HUMANITARIAN','SCIENCE')),
        area_level TEXT NOT NULL CHECK (area_level IN ('POSTCODE','BOROUGH','CITY','COUNTRY','CONTINENT','WORLD','UNIVERSE')),
        location_label TEXT NOT NULL,
        title TEXT NOT NULL,
        summary TEXT NOT NULL,
        source_name TEXT NOT NULL,
        source_url TEXT NOT NULL,
        source_type TEXT NOT NULL CHECK (source_type IN ('OFFICIAL','REPUTABLE','LOCAL_WITNESS','CHARITY','UNKNOWN')),
        observed_at TIMESTAMPTZ NOT NULL,
        expires_at TIMESTAMPTZ,
        verification_status TEXT NOT NULL CHECK (verification_status IN ('VERIFIED','DEVELOPING','UNKNOWN','CORRECTED')),
        risk_level TEXT NOT NULL CHECK (risk_level IN ('GREEN','AMBER','RED')),
        human_impact TEXT NOT NULL DEFAULT '',
        safe_action TEXT NOT NULL DEFAULT '',
        avoid_action TEXT NOT NULL DEFAULT '',
        youth_safe BOOLEAN NOT NULL DEFAULT FALSE,
        state TEXT NOT NULL DEFAULT 'DRAFT' CHECK (state IN ('DRAFT','ACTIVE','ARCHIVED','CORRECTED')),
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        CHECK (expires_at IS NULL OR expires_at > observed_at))""",
    """CREATE INDEX IF NOT EXISTS ix_world_signals_public
        ON oap_world_signals(kind, area_level, state, risk_level, observed_at DESC)""",
    """CREATE TABLE IF NOT EXISTS oap_civic_voice_items (
        civic_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        area_level TEXT NOT NULL CHECK (area_level IN ('POSTCODE','BOROUGH','CITY','COUNTRY','CONTINENT','WORLD')),
        location_label TEXT NOT NULL,
        issue_title TEXT NOT NULL,
        human_impact TEXT NOT NULL,
        verified_sources TEXT NOT NULL,
        official_action_url TEXT NOT NULL,
        deadline TIMESTAMPTZ,
        risk_level TEXT NOT NULL CHECK (risk_level IN ('GREEN','AMBER','RED')),
        youth_safe BOOLEAN NOT NULL DEFAULT FALSE,
        oap_summary TEXT NOT NULL,
        admin_notes TEXT NOT NULL DEFAULT '',
        state TEXT NOT NULL DEFAULT 'RESEARCHING' CHECK (state IN ('RESEARCHING','ACTIVE','CLOSED','REVIEWED')),
        official_channel BOOLEAN NOT NULL DEFAULT TRUE CHECK (official_channel=TRUE),
        non_binding BOOLEAN NOT NULL DEFAULT TRUE CHECK (non_binding=TRUE),
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
    """CREATE INDEX IF NOT EXISTS ix_civic_voice_public
        ON oap_civic_voice_items(area_level, state, risk_level, deadline)""",
    """CREATE TABLE IF NOT EXISTS oap_mentorship_guides (
        guide_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        audience TEXT NOT NULL CHECK (audience IN ('YOUTH','ADULT','BUSINESS','COMMUNITY_CAPTAIN')),
        title TEXT NOT NULL,
        explanation TEXT NOT NULL,
        safe_actions TEXT NOT NULL,
        no_go_warnings TEXT NOT NULL,
        official_links TEXT NOT NULL DEFAULT '',
        youth_safe BOOLEAN NOT NULL DEFAULT FALSE,
        state TEXT NOT NULL DEFAULT 'DRAFT' CHECK (state IN ('DRAFT','ACTIVE','ARCHIVED')),
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
    """CREATE INDEX IF NOT EXISTS ix_mentorship_public
        ON oap_mentorship_guides(audience, state, updated_at DESC)""",
    """CREATE TABLE IF NOT EXISTS oap_signal_corrections (
        correction_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        signal_id UUID NOT NULL REFERENCES oap_world_signals(signal_id) ON DELETE CASCADE,
        correction_text TEXT NOT NULL,
        source_url TEXT NOT NULL,
        human_approved BOOLEAN NOT NULL DEFAULT TRUE CHECK (human_approved=TRUE),
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
    """CREATE TABLE IF NOT EXISTS oap_signal_audit_logs (
        audit_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        signal_id UUID REFERENCES oap_world_signals(signal_id) ON DELETE SET NULL,
        event_type TEXT NOT NULL,
        actor_role TEXT NOT NULL DEFAULT 'HUMAN_AUTHORITY',
        decision TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
    """CREATE INDEX IF NOT EXISTS ix_signal_audit_created
        ON oap_signal_audit_logs(created_at DESC)""",
)
SAFE_SIGNALS_MIGRATION_CHECKSUM = hashlib.sha256(
    "\n".join(SAFE_SIGNALS_SCHEMA_STATEMENTS).encode()
).hexdigest()
SAFE_SIGNALS_TABLES = frozenset(
    {
        "oap_world_signals",
        "oap_civic_voice_items",
        "oap_mentorship_guides",
        "oap_signal_corrections",
        "oap_signal_audit_logs",
    }
)


def _https(value: object, field: str) -> str:
    text = str(value or "").strip()
    parsed = urlparse(text)
    if parsed.scheme != "https" or not parsed.netloc:
        raise ValueError(f"{field}_must_be_https")
    return text


def _text(value: object, field: str, maximum: int, *, required: bool = True) -> str:
    text = " ".join(str(value or "").strip().split())
    if required and not text:
        raise ValueError(f"{field}_required")
    if len(text) > maximum:
        raise ValueError(f"{field}_too_long")
    return text


def _choice(value: object, field: str, allowed: frozenset[str]) -> str:
    normalized = str(value or "").strip().upper()
    if normalized not in allowed:
        raise ValueError(f"invalid_{field}")
    return normalized


def _timestamp(value: object, field: str) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    else:
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except (TypeError, ValueError) as exc:
            raise ValueError(f"invalid_{field}") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _optional_timestamp(value: object, field: str) -> datetime | None:
    if value in (None, ""):
        return None
    return _timestamp(value, field)


def _uuid(value: object, field: str) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(f"invalid_{field}") from exc


def _require_human(payload: dict[str, Any]) -> None:
    if payload.get("human_authority_approved") is not True:
        raise PermissionError("human_authority_approval_required")


def _enforce_no_go_flags(payload: dict[str, Any]) -> None:
    blocked = (
        "legal_advice",
        "financial_advice",
        "binding_vote",
        "fake_signature",
        "pressure_campaign",
        "targets_individual",
        "precise_person_location",
        "youth_campaign_recruitment",
        "autonomous_action",
    )
    if any(payload.get(flag) is True for flag in blocked):
        raise PermissionError("safe_signals_no_go_boundary")


def schema_status() -> dict[str, Any]:
    result = {
        "migration": SAFE_SIGNALS_MIGRATION_VERSION,
        "checksum": SAFE_SIGNALS_MIGRATION_CHECKSUM,
        "schema_ready": False,
        "tables": 0,
        "expected_tables": len(SAFE_SIGNALS_TABLES),
        "error": None,
    }
    base = postgres_db.postgres_status()
    if not base.get("initialized"):
        result["error"] = "base_postgres_not_ready"
        return result
    try:
        with postgres_db.connect(readonly=True) as connection:
            rows = connection.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema='public'"
            ).fetchall()
            tables = {str(row[0]) for row in rows}
            result["tables"] = len(SAFE_SIGNALS_TABLES & tables)
            if not SAFE_SIGNALS_TABLES <= tables:
                result["error"] = "safe_signals_schema_pending"
                return result
            migration = connection.execute(
                "SELECT checksum FROM oap_schema_migrations WHERE version=%s",
                (SAFE_SIGNALS_MIGRATION_VERSION,),
            ).fetchone()
            if migration is None or str(migration[0]) != SAFE_SIGNALS_MIGRATION_CHECKSUM:
                result["error"] = "safe_signals_migration_not_verified"
                return result
        result["schema_ready"] = True
        return result
    except Exception:  # noqa: BLE001
        result["error"] = "safe_signals_store_unavailable"
        return result


def init_schema(*, assume_yes: bool = False, dry_run: bool = False) -> dict[str, Any]:
    """Apply v0.3 only after explicit Human Authority approval."""

    if not assume_yes:
        raise RuntimeError("Explicit human approval required: pass --yes")
    if dry_run:
        return {
            "dry_run": True,
            "migration": SAFE_SIGNALS_MIGRATION_VERSION,
            "checksum": SAFE_SIGNALS_MIGRATION_CHECKSUM,
            "tables": len(SAFE_SIGNALS_TABLES),
        }
    with postgres_db.connect() as connection:
        connection.execute("SELECT pg_advisory_xact_lock(%s)", (25800009,))
        row = connection.execute(
            "SELECT checksum FROM oap_schema_migrations WHERE version=%s",
            (SAFE_SIGNALS_MIGRATION_VERSION,),
        ).fetchone()
        if row is not None and str(row[0]) != SAFE_SIGNALS_MIGRATION_CHECKSUM:
            raise RuntimeError("Applied Safe Signals migration checksum mismatch")
        if row is None:
            for statement in SAFE_SIGNALS_SCHEMA_STATEMENTS:
                connection.execute(statement)
            connection.execute(
                "INSERT INTO oap_schema_migrations(version,checksum) VALUES (%s,%s)",
                (SAFE_SIGNALS_MIGRATION_VERSION, SAFE_SIGNALS_MIGRATION_CHECKSUM),
            )
        connection.commit()
    return schema_status()


def public_signals(
    *, kind: object = None, area_level: object = None, youth_safe: bool = False, limit: int = 50
) -> dict[str, Any]:
    schema = schema_status()
    if not schema["schema_ready"]:
        return {"component": "OAP Safe Signals", "ready": False, "items": [], "count": 0}
    clauses = ["state='ACTIVE'", "risk_level IN ('GREEN','AMBER')"]
    params: list[object] = []
    if kind:
        clauses.append("kind=%s")
        params.append(_choice(kind, "signal_kind", SIGNAL_KINDS))
    if area_level:
        clauses.append("area_level=%s")
        params.append(_choice(area_level, "area_level", AREA_LEVELS))
    if youth_safe:
        clauses.append("youth_safe=TRUE")
    params.append(max(1, min(int(limit), 100)))
    query = f"""SELECT signal_id,kind,area_level,location_label,title,summary,
                       source_name,source_url,source_type,observed_at,expires_at,
                       verification_status,risk_level,human_impact,safe_action,
                       avoid_action,youth_safe,state
                FROM oap_world_signals WHERE {' AND '.join(clauses)}
                  AND (expires_at IS NULL OR expires_at>CURRENT_TIMESTAMP)
                ORDER BY observed_at DESC LIMIT %s"""
    with postgres_db.connect(readonly=True) as connection:
        rows = connection.execute(query, tuple(params)).fetchall()
    items = [
        {
            "signal_id": str(row[0]),
            "kind": str(row[1]),
            "area_level": str(row[2]),
            "location_label": str(row[3]),
            "title": str(row[4]),
            "summary": str(row[5]),
            "source_name": str(row[6]),
            "source_url": str(row[7]),
            "source_type": str(row[8]),
            "observed_at": row[9].isoformat(),
            "expires_at": row[10].isoformat() if row[10] else None,
            "verification_status": str(row[11]),
            "risk_level": str(row[12]),
            "human_impact": str(row[13]),
            "safe_action": str(row[14]),
            "avoid_action": str(row[15]),
            "youth_safe": bool(row[16]),
            "state": str(row[17]),
        }
        for row in rows
    ]
    return {
        "component": "OAP Safe Signals",
        "ready": True,
        "items": items,
        "count": len(items),
        "public_promise": PUBLIC_PROMISE,
        "binding_vote": False,
        "legal_advice": False,
        "financial_advice": False,
        "autonomous_action": False,
    }


def public_civic_voice(*, limit: int = 50) -> dict[str, Any]:
    if not schema_status()["schema_ready"]:
        return {"component": "OAP Civic Voice", "ready": False, "items": [], "count": 0}
    with postgres_db.connect(readonly=True) as connection:
        rows = connection.execute(
            """SELECT civic_id,area_level,location_label,issue_title,human_impact,
                      verified_sources,official_action_url,deadline,risk_level,youth_safe,
                      oap_summary,state
               FROM oap_civic_voice_items
               WHERE state='ACTIVE' AND risk_level IN ('GREEN','AMBER')
                 AND (deadline IS NULL OR deadline>CURRENT_TIMESTAMP)
               ORDER BY deadline NULLS LAST,updated_at DESC LIMIT %s""",
            (max(1, min(int(limit), 100)),),
        ).fetchall()
    items = [
        {
            "civic_id": str(row[0]),
            "area_level": str(row[1]),
            "location_label": str(row[2]),
            "issue_title": str(row[3]),
            "human_impact": str(row[4]),
            "verified_sources": str(row[5]),
            "official_action_url": str(row[6]),
            "deadline": row[7].isoformat() if row[7] else None,
            "risk_level": str(row[8]),
            "youth_safe": bool(row[9]),
            "oap_summary": str(row[10]),
            "state": str(row[11]),
            "official_channel": True,
            "non_binding": True,
        }
        for row in rows
    ]
    return {
        "component": "OAP Civic Voice",
        "ready": True,
        "items": items,
        "count": len(items),
        "official_channels_only": True,
        "non_binding": True,
    }


def public_mentorship(*, audience: object = None, limit: int = 50) -> dict[str, Any]:
    if not schema_status()["schema_ready"]:
        return {"component": "OAP Mentorship", "ready": False, "items": [], "count": 0}
    clauses = ["state='ACTIVE'"]
    params: list[object] = []
    if audience:
        audience_value = _choice(audience, "mentor_audience", MENTOR_AUDIENCES)
        clauses.append("audience=%s")
        params.append(audience_value)
        if audience_value == "YOUTH":
            clauses.append("youth_safe=TRUE")
    params.append(max(1, min(int(limit), 100)))
    with postgres_db.connect(readonly=True) as connection:
        rows = connection.execute(
            f"""SELECT guide_id,audience,title,explanation,safe_actions,no_go_warnings,
                       official_links,youth_safe
                FROM oap_mentorship_guides WHERE {' AND '.join(clauses)}
                ORDER BY updated_at DESC LIMIT %s""",
            tuple(params),
        ).fetchall()
    items = [
        {
            "guide_id": str(row[0]),
            "audience": str(row[1]),
            "title": str(row[2]),
            "explanation": str(row[3]),
            "safe_actions": str(row[4]),
            "no_go_warnings": str(row[5]),
            "official_links": str(row[6]),
            "youth_safe": bool(row[7]),
        }
        for row in rows
    ]
    return {"component": "OAP Mentorship", "ready": True, "items": items, "count": len(items)}


class SafeSignalsStore:
    """Founder/Human-Authority bounded write operations."""

    def create_signal(self, payload: dict[str, Any]) -> dict[str, Any]:
        _require_human(payload)
        _enforce_no_go_flags(payload)
        kind = _choice(payload.get("kind"), "signal_kind", SIGNAL_KINDS)
        area = _choice(payload.get("area_level"), "area_level", AREA_LEVELS)
        location = _text(payload.get("location_label"), "location_label", 180)
        title = _text(payload.get("title"), "title", 220)
        summary = _text(payload.get("summary"), "summary", 4000)
        source_name = _text(payload.get("source_name"), "source_name", 180)
        source_url = _https(payload.get("source_url"), "source_url")
        source_type = _choice(payload.get("source_type"), "source_type", SOURCE_TYPES)
        observed_at = _timestamp(payload.get("observed_at"), "observed_at")
        expires_at = _optional_timestamp(payload.get("expires_at"), "expires_at")
        verification = _choice(
            payload.get("verification_status"), "verification_status", VERIFICATION_STATES
        )
        risk = _choice(payload.get("risk_level"), "risk_level", RISK_LEVELS)
        youth_safe = payload.get("youth_safe") is True
        with postgres_db.connect() as connection:
            row = connection.execute(
                """INSERT INTO oap_world_signals(
                       kind,area_level,location_label,title,summary,source_name,source_url,
                       source_type,observed_at,expires_at,verification_status,risk_level,
                       human_impact,safe_action,avoid_action,youth_safe,state)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'DRAFT')
                   RETURNING signal_id,state""",
                (
                    kind,
                    area,
                    location,
                    title,
                    summary,
                    source_name,
                    source_url,
                    source_type,
                    observed_at,
                    expires_at,
                    verification,
                    risk,
                    _text(payload.get("human_impact"), "human_impact", 2000, required=False),
                    _text(payload.get("safe_action"), "safe_action", 2000, required=False),
                    _text(payload.get("avoid_action"), "avoid_action", 2000, required=False),
                    youth_safe,
                ),
            ).fetchone()
            connection.execute(
                "INSERT INTO oap_signal_audit_logs(signal_id,event_type,decision) VALUES (%s,'CREATE','DRAFT')",
                (row[0],),
            )
            connection.commit()
        return {"signal_id": str(row[0]), "state": str(row[1]), "risk_level": risk}

    def activate_signal(self, payload: dict[str, Any]) -> dict[str, Any]:
        _require_human(payload)
        _enforce_no_go_flags(payload)
        signal_id = _uuid(payload.get("signal_id"), "signal_id")
        with postgres_db.connect() as connection:
            current = connection.execute(
                "SELECT risk_level,verification_status,state FROM oap_world_signals WHERE signal_id=%s FOR UPDATE",
                (signal_id,),
            ).fetchone()
            if current is None:
                raise ValueError("signal_not_found")
            if str(current[0]) == "RED":
                raise PermissionError("red_signal_cannot_be_public")
            if str(current[1]) == "UNKNOWN":
                raise PermissionError("unknown_signal_cannot_be_public")
            connection.execute(
                "UPDATE oap_world_signals SET state='ACTIVE',updated_at=CURRENT_TIMESTAMP WHERE signal_id=%s",
                (signal_id,),
            )
            connection.execute(
                "INSERT INTO oap_signal_audit_logs(signal_id,event_type,decision) VALUES (%s,'ACTIVATE','ACTIVE')",
                (signal_id,),
            )
            connection.commit()
        return {"signal_id": signal_id, "state": "ACTIVE"}

    def add_correction(self, payload: dict[str, Any]) -> dict[str, Any]:
        _require_human(payload)
        signal_id = _uuid(payload.get("signal_id"), "signal_id")
        correction = _text(payload.get("correction_text"), "correction_text", 4000)
        source_url = _https(payload.get("source_url"), "source_url")
        with postgres_db.connect() as connection:
            row = connection.execute(
                """INSERT INTO oap_signal_corrections(signal_id,correction_text,source_url)
                   VALUES (%s,%s,%s) RETURNING correction_id""",
                (signal_id, correction, source_url),
            ).fetchone()
            connection.execute(
                """UPDATE oap_world_signals SET verification_status='CORRECTED',state='CORRECTED',
                          updated_at=CURRENT_TIMESTAMP WHERE signal_id=%s""",
                (signal_id,),
            )
            connection.execute(
                "INSERT INTO oap_signal_audit_logs(signal_id,event_type,decision) VALUES (%s,'CORRECT','CORRECTED')",
                (signal_id,),
            )
            connection.commit()
        return {"signal_id": signal_id, "correction_id": str(row[0]), "state": "CORRECTED"}

    def create_civic_item(self, payload: dict[str, Any]) -> dict[str, Any]:
        _require_human(payload)
        _enforce_no_go_flags(payload)
        if payload.get("official_channel") is not True or payload.get("non_binding") is not True:
            raise PermissionError("official_non_binding_civic_channel_required")
        area = _choice(payload.get("area_level"), "area_level", AREA_LEVELS - {"UNIVERSE"})
        risk = _choice(payload.get("risk_level"), "risk_level", RISK_LEVELS)
        if risk == "RED":
            raise PermissionError("red_civic_item_cannot_be_public")
        action_url = _https(payload.get("official_action_url"), "official_action_url")
        deadline = _optional_timestamp(payload.get("deadline"), "deadline")
        state = "ACTIVE" if payload.get("activate") is True else "RESEARCHING"
        with postgres_db.connect() as connection:
            row = connection.execute(
                """INSERT INTO oap_civic_voice_items(
                       area_level,location_label,issue_title,human_impact,verified_sources,
                       official_action_url,deadline,risk_level,youth_safe,oap_summary,
                       admin_notes,state,official_channel,non_binding)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,TRUE,TRUE)
                   RETURNING civic_id,state""",
                (
                    area,
                    _text(payload.get("location_label"), "location_label", 180),
                    _text(payload.get("issue_title"), "issue_title", 240),
                    _text(payload.get("human_impact"), "human_impact", 3000),
                    _text(payload.get("verified_sources"), "verified_sources", 4000),
                    action_url,
                    deadline,
                    risk,
                    payload.get("youth_safe") is True,
                    _text(payload.get("oap_summary"), "oap_summary", 4000),
                    _text(payload.get("admin_notes"), "admin_notes", 2000, required=False),
                    state,
                ),
            ).fetchone()
            connection.commit()
        return {"civic_id": str(row[0]), "state": str(row[1]), "non_binding": True}

    def create_mentorship_guide(self, payload: dict[str, Any]) -> dict[str, Any]:
        _require_human(payload)
        _enforce_no_go_flags(payload)
        audience = _choice(payload.get("audience"), "mentor_audience", MENTOR_AUDIENCES)
        youth_safe = payload.get("youth_safe") is True
        if audience == "YOUTH" and not youth_safe:
            raise PermissionError("youth_guide_must_be_youth_safe")
        state = "ACTIVE" if payload.get("activate") is True else "DRAFT"
        with postgres_db.connect() as connection:
            row = connection.execute(
                """INSERT INTO oap_mentorship_guides(
                       audience,title,explanation,safe_actions,no_go_warnings,
                       official_links,youth_safe,state)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s) RETURNING guide_id,state""",
                (
                    audience,
                    _text(payload.get("title"), "title", 220),
                    _text(payload.get("explanation"), "explanation", 5000),
                    _text(payload.get("safe_actions"), "safe_actions", 4000),
                    _text(payload.get("no_go_warnings"), "no_go_warnings", 4000),
                    _text(payload.get("official_links"), "official_links", 4000, required=False),
                    youth_safe,
                    state,
                ),
            ).fetchone()
            connection.commit()
        return {"guide_id": str(row[0]), "state": str(row[1]), "audience": audience}


def status() -> dict[str, Any]:
    schema = schema_status()
    counts = {"signals": 0, "civic": 0, "mentorship": 0}
    if schema["schema_ready"]:
        try:
            with postgres_db.connect(readonly=True) as connection:
                counts["signals"] = int(
                    connection.execute("SELECT COUNT(*) FROM oap_world_signals WHERE state='ACTIVE'").fetchone()[0]
                )
                counts["civic"] = int(
                    connection.execute("SELECT COUNT(*) FROM oap_civic_voice_items WHERE state='ACTIVE'").fetchone()[0]
                )
                counts["mentorship"] = int(
                    connection.execute("SELECT COUNT(*) FROM oap_mentorship_guides WHERE state='ACTIVE'").fetchone()[0]
                )
        except Exception:  # noqa: BLE001
            schema["schema_ready"] = False
            schema["error"] = "safe_signals_status_query_failed"
    return {
        "component": "OAP Safe Signals v0.3",
        "revision": SAFE_SIGNALS_REVISION,
        "software_ready": True,
        "schema": schema,
        "counts": counts,
        "boards": ("signals", "weather", "news-facts", "civic-voice", "mentorship"),
        "public_promise": PUBLIC_PROMISE,
        "postcode_to_planet": True,
        "weather_preparation_not_fear": True,
        "news_fact_checking": True,
        "official_civic_channels_only": True,
        "community_polls_binding": False,
        "legal_advice": False,
        "financial_advice": False,
        "debt_evasion_advice": False,
        "political_manipulation": False,
        "fake_petitions": False,
        "youth_campaign_recruitment": False,
        "autonomous_action": False,
        "creates_intelligence_worlds": False,
        "creates_agents": False,
        "creates_brain": False,
        "guardian_gate_required": True,
        "human_authority_final": True,
    }
