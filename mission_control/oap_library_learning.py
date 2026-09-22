"""Private, source-bound learning records for OAP Library.

Schema activation is explicit. Records remain private to one authenticated OAP
identity; this module does not create public URLs, social feeds or automatic
shares. A member must deliberately export or invoke their device share sheet.
"""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from collections.abc import Mapping, Sequence
from typing import Any

from . import oap_library, postgres_db

SCHEMA_VERSION = "oap_library_learning_v1"
MAX_REFLECTION_CHARS = 600
MAX_RECORDS_PER_MEMBER = 100
RIGHTS_BASIS = "MEMBER_AUTHORED_REFLECTION_WITH_CITED_OAP_FACT"

SCHEMA_SQL = (
    """CREATE TABLE IF NOT EXISTS oap_library_learning_records (
        record_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        identity_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        book_id TEXT NOT NULL CHECK (book_id = 'food-book'),
        food_id TEXT NOT NULL,
        area_id TEXT NOT NULL,
        fact_snapshot TEXT NOT NULL,
        reflection TEXT NOT NULL
            CHECK (char_length(reflection) BETWEEN 1 AND 600),
        sources_json JSONB NOT NULL
            CHECK (jsonb_typeof(sources_json) = 'array'),
        rights_basis TEXT NOT NULL
            CHECK (rights_basis = 'MEMBER_AUTHORED_REFLECTION_WITH_CITED_OAP_FACT'),
        rights_attested BOOLEAN NOT NULL CHECK (rights_attested IS TRUE),
        visibility TEXT NOT NULL DEFAULT 'PRIVATE'
            CHECK (visibility = 'PRIVATE'),
        content_hash CHAR(64) NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)""",
    """CREATE INDEX IF NOT EXISTS idx_library_learning_identity_created
        ON oap_library_learning_records(identity_id, created_at DESC)""",
)

_CONTROL_CHARACTERS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


class LibraryLearningUnavailable(RuntimeError):
    """Raised when the private learning store cannot safely complete a request."""


def _uuid(value: object, code: str) -> str:
    try:
        return str(uuid.UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(code) from exc


def _reflection(value: object) -> str:
    if not isinstance(value, str):
        raise TypeError("reflection_required")
    reflection = value.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not reflection:
        raise ValueError("reflection_required")
    if len(reflection) > MAX_REFLECTION_CHARS:
        raise ValueError("reflection_too_long")
    if _CONTROL_CHARACTERS.search(reflection):
        raise ValueError("reflection_contains_control_characters")
    return reflection


def _canonical_payload(record: Mapping[str, object]) -> bytes:
    sources = record.get("sources")
    if not isinstance(sources, Sequence) or isinstance(sources, (str, bytes)):
        raise TypeError("learning_sources_invalid")
    payload = {
        "book_id": str(record.get("book_id") or ""),
        "food_id": str(record.get("food_id") or ""),
        "area_id": str(record.get("area_id") or ""),
        "fact": str(record.get("fact") or ""),
        "reflection": str(record.get("reflection") or ""),
        "sources": list(sources),
        "rights_basis": str(record.get("rights_basis") or ""),
        "visibility": str(record.get("visibility") or ""),
    }
    return json.dumps(
        payload,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")


def _content_hash(record: Mapping[str, object]) -> str:
    return hashlib.sha256(_canonical_payload(record)).hexdigest()


def prepare_record(
    *,
    food_id: object,
    area_id: object,
    reflection: object,
    rights_attested: object,
) -> dict[str, object]:
    """Validate user input and attach only catalogue-controlled facts/sources."""

    if rights_attested is not True:
        raise PermissionError("rights_attestation_required")
    learning = oap_library.food_learning_card(food_id, area_id)
    record = {
        **learning,
        "reflection": _reflection(reflection),
        "rights_basis": RIGHTS_BASIS,
        "rights_attested": True,
        "visibility": "PRIVATE",
    }
    record["content_hash"] = _content_hash(record)
    return record


def _source_list(value: object) -> list[dict[str, str]]:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError as exc:
            raise LibraryLearningUnavailable("learning_sources_invalid") from exc
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise LibraryLearningUnavailable("learning_sources_invalid")
    sources: list[dict[str, str]] = []
    for item in value:
        if not isinstance(item, Mapping):
            raise LibraryLearningUnavailable("learning_sources_invalid")
        source_id = str(item.get("id") or "")
        name = str(item.get("name") or "")
        url = str(item.get("url") or "")
        if not source_id or not name or not url.startswith("https://"):
            raise LibraryLearningUnavailable("learning_sources_invalid")
        sources.append({"id": source_id, "name": name, "url": url})
    if not sources:
        raise LibraryLearningUnavailable("learning_sources_invalid")
    return sources


def export_text(record: Mapping[str, object]) -> str:
    """Render a bounded card with fact, member reflection and source trail."""

    sources = _source_list(record.get("sources"))
    source_lines = "\n".join(
        f"- {source['name']}: {source['url']}" for source in sources
    )
    return (
        "OAP LIBRARY · FOOD BOOK\n\n"
        f"SOURCE-BACKED FACT\n{record.get('fact', '')}\n\n"
        f"MY REFLECTION\n{record.get('reflection', '')}\n\n"
        f"OFFICIAL SOURCES\n{source_lines}\n\n"
        "Educational information only. Food supports the whole body and this "
        "card does not diagnose or treat illness.\n\n"
        "BORN LOCAL. BUILT GLOBAL. EARTH IS OUR TURF."
    )


def _public_record(record: Mapping[str, object]) -> dict[str, object]:
    public = dict(record)
    public["sources"] = _source_list(public.get("sources"))
    public["export_text"] = export_text(public)
    return public


def init_schema(*, assume_yes: bool = False, dry_run: bool = False) -> dict[str, Any]:
    if not assume_yes and not dry_run:
        raise PermissionError("explicit_confirmation_required")
    if dry_run:
        return {
            "version": SCHEMA_VERSION,
            "statements": list(SCHEMA_SQL),
            "applied": False,
        }
    try:
        with postgres_db.connect() as connection:
            connection.execute(
                "SELECT pg_advisory_xact_lock(hashtext('oap_library_learning_v1'))"
            )
            for statement in SCHEMA_SQL:
                connection.execute(statement)
            connection.commit()
    except Exception as exc:
        raise LibraryLearningUnavailable("learning_schema_failed") from exc
    return {"version": SCHEMA_VERSION, "applied": True}


def status() -> dict[str, object]:
    result: dict[str, object] = {
        "configured": postgres_db.configured(),
        "schema_ready": False,
        "ready": False,
        "first_party": True,
        "visibility": "PRIVATE",
        "automatic_sharing": False,
    }
    if not result["configured"]:
        return result
    try:
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(
                """SELECT 1 FROM information_schema.tables
                   WHERE table_schema='public'
                     AND table_name='oap_library_learning_records'"""
            ).fetchone()
        result["schema_ready"] = row is not None
    except Exception:  # noqa: BLE001 - readiness must fail closed.
        return result
    result["ready"] = bool(result["schema_ready"])
    return result


def create_record(
    identity_id: object,
    *,
    food_id: object,
    area_id: object,
    reflection: object,
    rights_attested: object,
    display_name: object = "OAP Member",
) -> dict[str, object]:
    identity = _uuid(identity_id, "invalid_identity")
    record = prepare_record(
        food_id=food_id,
        area_id=area_id,
        reflection=reflection,
        rights_attested=rights_attested,
    )
    sources_json = json.dumps(
        record["sources"], ensure_ascii=False, separators=(",", ":")
    )
    try:
        with postgres_db.connect() as connection:
            connection.execute(
                """INSERT INTO users(id,username,display_name,status)
                   VALUES (%s,%s,%s,'active')
                   ON CONFLICT (id) DO UPDATE SET
                     display_name=COALESCE(users.display_name,EXCLUDED.display_name),
                     status='active',updated_at=CURRENT_TIMESTAMP""",
                (
                    identity,
                    f"oap-library-{identity.replace('-', '')}",
                    str(display_name or "OAP Member")[:120],
                ),
            )
            count_row = connection.execute(
                """SELECT COUNT(*) FROM oap_library_learning_records
                   WHERE identity_id=%s""",
                (identity,),
            ).fetchone()
            if count_row and int(count_row[0]) >= MAX_RECORDS_PER_MEMBER:
                raise ValueError("learning_record_limit_reached")
            row = connection.execute(
                """INSERT INTO oap_library_learning_records(
                       identity_id,book_id,food_id,area_id,fact_snapshot,
                       reflection,sources_json,rights_basis,rights_attested,
                       visibility,content_hash)
                   VALUES (%s,%s,%s,%s,%s,%s,%s::jsonb,%s,TRUE,%s,%s)
                   RETURNING record_id,created_at""",
                (
                    identity,
                    record["book_id"],
                    record["food_id"],
                    record["area_id"],
                    record["fact"],
                    record["reflection"],
                    sources_json,
                    record["rights_basis"],
                    record["visibility"],
                    record["content_hash"],
                ),
            ).fetchone()
            connection.commit()
    except (PermissionError, TypeError, ValueError):
        raise
    except Exception as exc:
        raise LibraryLearningUnavailable("learning_record_write_failed") from exc
    if row is None:
        raise LibraryLearningUnavailable("learning_record_write_failed")
    created_at = row[1].isoformat() if hasattr(row[1], "isoformat") else str(row[1])
    return _public_record(
        {**record, "record_id": str(row[0]), "created_at": created_at}
    )


def list_records(identity_id: object, *, limit: int = 50) -> list[dict[str, object]]:
    identity = _uuid(identity_id, "invalid_identity")
    safe_limit = max(1, min(int(limit), 50))
    try:
        with postgres_db.connect(readonly=True) as connection:
            rows = connection.execute(
                """SELECT record_id,book_id,food_id,area_id,fact_snapshot,
                          reflection,sources_json,rights_basis,rights_attested,
                          visibility,content_hash,created_at
                   FROM oap_library_learning_records
                   WHERE identity_id=%s
                   ORDER BY created_at DESC LIMIT %s""",
                (identity, safe_limit),
            ).fetchall()
    except Exception as exc:
        raise LibraryLearningUnavailable("learning_record_read_failed") from exc

    records: list[dict[str, object]] = []
    for row in rows:
        created_at = row[11].isoformat() if hasattr(row[11], "isoformat") else str(row[11])
        record: dict[str, object] = {
            "record_id": str(row[0]),
            "book_id": str(row[1]),
            "food_id": str(row[2]),
            "area_id": str(row[3]),
            "fact": str(row[4]),
            "reflection": str(row[5]),
            "sources": _source_list(row[6]),
            "rights_basis": str(row[7]),
            "rights_attested": bool(row[8]),
            "visibility": str(row[9]),
            "content_hash": str(row[10]),
            "created_at": created_at,
        }
        if not record["rights_attested"] or record["visibility"] != "PRIVATE":
            raise LibraryLearningUnavailable("learning_record_boundary_failed")
        if not hashlib.sha256(_canonical_payload(record)).hexdigest() == record["content_hash"]:
            raise LibraryLearningUnavailable("learning_record_integrity_failed")
        records.append(_public_record(record))
    return records


def delete_record(identity_id: object, record_id: object) -> bool:
    identity = _uuid(identity_id, "invalid_identity")
    record = _uuid(record_id, "invalid_record")
    try:
        with postgres_db.connect() as connection:
            row = connection.execute(
                """DELETE FROM oap_library_learning_records
                   WHERE record_id=%s AND identity_id=%s RETURNING record_id""",
                (record, identity),
            ).fetchone()
            connection.commit()
    except Exception as exc:
        raise LibraryLearningUnavailable("learning_record_delete_failed") from exc
    return row is not None
