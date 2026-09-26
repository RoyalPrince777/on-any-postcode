"""First-party OAP Knowledge Mind contract.

This module defines the bounded knowledge-card model shared by My World, Explorer,
Registry and SMI. It is intentionally non-public and non-migrating by default:
The Vault is private by default, publication requires Human Authority, and schema
creation requires explicit approval.

No private chain-of-thought, hidden prompts, credentials or unrelated personal
data belong in OAP Knowledge.
"""
from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from . import postgres_db

KNOWLEDGE_MIGRATION_VERSION = "0001_oap_knowledge_mind"
KNOWLEDGE_OWNER = "My World"
KNOWLEDGE_SYSTEM_NAME = "OAP Knowledge"
PRIVATE_SURFACE_NAME = "The Vault"

EVIDENCE_STATES = frozenset({"RAW", "SUMMARISED", "SUPPORTED", "CERTIFIED"})
VISIBILITIES = frozenset({"PRIVATE", "UNLISTED", "PUBLIC"})
DEFAULT_VISIBILITY = "PRIVATE"

KNOWLEDGE_TABLES = frozenset(
    {
        "oap_knowledge_cards",
        "oap_knowledge_sources",
        "oap_knowledge_collections",
        "oap_knowledge_collection_items",
        "oap_knowledge_topics",
        "oap_knowledge_card_topics",
        "oap_knowledge_relations",
        "oap_knowledge_places",
        "oap_knowledge_evidence",
        "oap_knowledge_history",
    }
)

KNOWLEDGE_SCHEMA_STATEMENTS = (
    """CREATE TABLE IF NOT EXISTS oap_knowledge_cards (
        card_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        owner_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        title TEXT NOT NULL,
        insight TEXT NOT NULL,
        summary TEXT,
        evidence_state TEXT NOT NULL DEFAULT 'RAW'
            CHECK (evidence_state IN ('RAW','SUMMARISED','SUPPORTED','CERTIFIED')),
        visibility TEXT NOT NULL DEFAULT 'PRIVATE'
            CHECK (visibility IN ('PRIVATE','UNLISTED','PUBLIC')),
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        deleted_at TIMESTAMPTZ
    )""",
    """CREATE INDEX IF NOT EXISTS ix_knowledge_cards_owner_created
        ON oap_knowledge_cards(owner_identity_id, created_at DESC)""",
    """CREATE TABLE IF NOT EXISTS oap_knowledge_sources (
        source_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        owner_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        card_id UUID NOT NULL REFERENCES oap_knowledge_cards(card_id) ON DELETE CASCADE,
        source_kind TEXT NOT NULL,
        source_ref TEXT NOT NULL,
        provenance TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS oap_knowledge_collections (
        collection_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        owner_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        title TEXT NOT NULL,
        visibility TEXT NOT NULL DEFAULT 'PRIVATE'
            CHECK (visibility IN ('PRIVATE','UNLISTED','PUBLIC')),
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS oap_knowledge_collection_items (
        collection_id UUID NOT NULL REFERENCES oap_knowledge_collections(collection_id)
            ON DELETE CASCADE,
        card_id UUID NOT NULL REFERENCES oap_knowledge_cards(card_id) ON DELETE CASCADE,
        position INTEGER NOT NULL CHECK (position > 0),
        added_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (collection_id, card_id),
        UNIQUE(collection_id, position)
    )""",
    """CREATE TABLE IF NOT EXISTS oap_knowledge_topics (
        topic_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        owner_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        name TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(owner_identity_id, name)
    )""",
    """CREATE TABLE IF NOT EXISTS oap_knowledge_card_topics (
        card_id UUID NOT NULL REFERENCES oap_knowledge_cards(card_id) ON DELETE CASCADE,
        topic_id UUID NOT NULL REFERENCES oap_knowledge_topics(topic_id) ON DELETE CASCADE,
        PRIMARY KEY (card_id, topic_id)
    )""",
    """CREATE TABLE IF NOT EXISTS oap_knowledge_relations (
        owner_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        from_card_id UUID NOT NULL REFERENCES oap_knowledge_cards(card_id) ON DELETE CASCADE,
        to_card_id UUID NOT NULL REFERENCES oap_knowledge_cards(card_id) ON DELETE CASCADE,
        relation_type TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (owner_identity_id, from_card_id, to_card_id, relation_type),
        CHECK (from_card_id <> to_card_id)
    )""",
    """CREATE TABLE IF NOT EXISTS oap_knowledge_places (
        card_id UUID NOT NULL REFERENCES oap_knowledge_cards(card_id) ON DELETE CASCADE,
        owner_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        postcode TEXT,
        borough_district TEXT,
        county_region TEXT,
        country TEXT,
        continent TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (card_id, owner_identity_id)
    )""",
    """CREATE TABLE IF NOT EXISTS oap_knowledge_evidence (
        evidence_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        owner_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        card_id UUID NOT NULL REFERENCES oap_knowledge_cards(card_id) ON DELETE CASCADE,
        evidence_ref TEXT NOT NULL,
        provenance TEXT NOT NULL,
        digest TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS oap_knowledge_history (
        history_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        owner_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        card_id UUID NOT NULL REFERENCES oap_knowledge_cards(card_id) ON DELETE CASCADE,
        action TEXT NOT NULL,
        from_visibility TEXT,
        to_visibility TEXT,
        receipt_ref TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
    )""",
)


@dataclass(frozen=True)
class KnowledgeCardInput:
    title: str
    insight: str
    summary: str | None = None
    evidence_state: str = "RAW"
    visibility: str = DEFAULT_VISIBILITY

    def validated(self) -> KnowledgeCardInput:
        title = self.title.strip()
        insight = self.insight.strip()
        summary = self.summary.strip() if isinstance(self.summary, str) else None
        state = self.evidence_state.strip().upper()
        visibility = self.visibility.strip().upper()
        if not title:
            raise ValueError("knowledge_title_required")
        if not insight:
            raise ValueError("knowledge_insight_required")
        if len(title) > 200:
            raise ValueError("knowledge_title_too_long")
        if len(insight) > 4000:
            raise ValueError("knowledge_insight_too_long")
        if summary is not None and len(summary) > 8000:
            raise ValueError("knowledge_summary_too_long")
        if state not in EVIDENCE_STATES:
            raise ValueError("invalid_knowledge_evidence_state")
        if visibility not in VISIBILITIES:
            raise ValueError("invalid_knowledge_visibility")
        return KnowledgeCardInput(
            title=title,
            insight=insight,
            summary=summary,
            evidence_state=state,
            visibility=visibility,
        )


def require_publication_approval(
    visibility: str,
    *,
    human_approved: bool = False,
) -> str:
    requested = str(visibility).strip().upper()
    if requested not in VISIBILITIES:
        raise ValueError("invalid_knowledge_visibility")
    if requested != "PRIVATE" and not human_approved:
        raise PermissionError("human_publication_approval_required")
    return requested


def validate_knowledge_contract(
    statements: Iterable[str] = KNOWLEDGE_SCHEMA_STATEMENTS,
) -> dict[str, Any]:
    sql = "\n".join(str(statement) for statement in statements)
    errors: list[str] = []
    for table in KNOWLEDGE_TABLES:
        if table not in sql:
            errors.append(f"Missing knowledge table: {table}")
    if "DEFAULT 'PRIVATE'" not in sql:
        errors.append("Knowledge must default private")
    if "owner_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE" not in sql:
        errors.append("Owner-scoped cascading identity boundary missing")
    for state in EVIDENCE_STATES:
        if state not in sql:
            errors.append(f"Missing evidence state: {state}")
    if "provenance" not in sql:
        errors.append("Provenance field missing")
    return {
        "passed": not errors,
        "errors": errors,
        "checks": {
            "tables": len(KNOWLEDGE_TABLES),
            "private_by_default": "DEFAULT 'PRIVATE'" in sql,
            "owner_scoped": "owner_identity_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE" in sql,
            "evidence_states": tuple(sorted(EVIDENCE_STATES)),
        },
    }


def public_contract() -> Mapping[str, Any]:
    return {
        "system": KNOWLEDGE_SYSTEM_NAME,
        "private_surface": PRIVATE_SURFACE_NAME,
        "owner": KNOWLEDGE_OWNER,
        "default_visibility": DEFAULT_VISIBILITY,
        "evidence_states": ("RAW", "SUMMARISED", "SUPPORTED", "CERTIFIED"),
        "my_world_owns_saved_knowledge": True,
        "explorer_may_discover_place_knowledge": True,
        "registry_owns_provenance": True,
        "smi_may_summarise_but_not_silently_certify": True,
        "human_approval_before_publication": True,
        "private_chain_of_thought_stored": False,
    }


def init_schema(*, human_approved: bool = False) -> tuple[str, ...]:
    """Return schema statements only after explicit Human Authority approval.

    Execution is deliberately left to the existing migration owner.
    """
    if not human_approved:
        raise RuntimeError("Explicit human approval required for OAP Knowledge schema")
    return KNOWLEDGE_SCHEMA_STATEMENTS


class KnowledgeUnavailable(RuntimeError):
    """Raised when private OAP Knowledge storage cannot safely complete."""


def _uuid(value: object, code: str) -> str:
    try:
        return str(UUID(str(value)))
    except (TypeError, ValueError, AttributeError) as exc:
        raise ValueError(code) from exc


def status() -> dict[str, object]:
    result: dict[str, object] = {
        "configured": postgres_db.configured(),
        "schema_ready": False,
        "ready": False,
        "first_party": True,
        "default_visibility": DEFAULT_VISIBILITY,
        "public_write_enabled": False,
    }
    if not result["configured"]:
        return result
    try:
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(
                """SELECT 1 FROM information_schema.tables
                   WHERE table_schema='public'
                     AND table_name='oap_knowledge_cards'"""
            ).fetchone()
        result["schema_ready"] = row is not None
    except Exception:  # noqa: BLE001 - readiness must fail closed.
        return result
    result["ready"] = bool(result["schema_ready"])
    return result


def _row_card(row: object) -> dict[str, object]:
    values = list(row)
    created_at = values[6]
    updated_at = values[7]
    return {
        "card_id": str(values[0]),
        "title": str(values[1]),
        "insight": str(values[2]),
        "summary": values[3],
        "evidence_state": str(values[4]),
        "visibility": str(values[5]),
        "created_at": created_at.isoformat() if hasattr(created_at, "isoformat") else str(created_at),
        "updated_at": updated_at.isoformat() if hasattr(updated_at, "isoformat") else str(updated_at),
    }


def create_card(
    identity_id: object,
    *,
    title: object,
    insight: object,
    summary: object = None,
) -> dict[str, object]:
    identity = _uuid(identity_id, "invalid_identity")
    card = KnowledgeCardInput(
        title=str(title or ""),
        insight=str(insight or ""),
        summary=None if summary is None else str(summary),
    ).validated()
    try:
        with postgres_db.connect() as connection:
            row = connection.execute(
                """INSERT INTO oap_knowledge_cards(
                       owner_identity_id,title,insight,summary,evidence_state,visibility)
                   VALUES (%s,%s,%s,%s,'RAW','PRIVATE')
                   RETURNING card_id,title,insight,summary,evidence_state,visibility,
                             created_at,updated_at""",
                (identity, card.title, card.insight, card.summary),
            ).fetchone()
            if row is None:
                raise KnowledgeUnavailable("knowledge_card_write_failed")
            connection.execute(
                """INSERT INTO oap_knowledge_history(
                       owner_identity_id,card_id,action,to_visibility)
                   VALUES (%s,%s,'CREATE','PRIVATE')""",
                (identity, row[0]),
            )
            connection.commit()
    except (TypeError, ValueError, PermissionError, KnowledgeUnavailable):
        raise
    except Exception as exc:
        raise KnowledgeUnavailable("knowledge_card_write_failed") from exc
    return _row_card(row)


def get_card(identity_id: object, card_id: object) -> dict[str, object] | None:
    identity = _uuid(identity_id, "invalid_identity")
    card = _uuid(card_id, "invalid_card")
    try:
        with postgres_db.connect(readonly=True) as connection:
            row = connection.execute(
                """SELECT card_id,title,insight,summary,evidence_state,visibility,
                          created_at,updated_at
                   FROM oap_knowledge_cards
                   WHERE owner_identity_id=%s AND card_id=%s AND deleted_at IS NULL""",
                (identity, card),
            ).fetchone()
    except Exception as exc:
        raise KnowledgeUnavailable("knowledge_card_read_failed") from exc
    return None if row is None else _row_card(row)


def list_cards(
    identity_id: object,
    *,
    query: object = "",
    limit: int = 50,
) -> list[dict[str, object]]:
    identity = _uuid(identity_id, "invalid_identity")
    text = str(query or "").strip()[:160]
    safe_limit = max(1, min(int(limit), 50))
    pattern = f"%{text}%"
    try:
        with postgres_db.connect(readonly=True) as connection:
            rows = connection.execute(
                """SELECT card_id,title,insight,summary,evidence_state,visibility,
                          created_at,updated_at
                   FROM oap_knowledge_cards
                   WHERE owner_identity_id=%s AND deleted_at IS NULL
                     AND (%s='' OR title ILIKE %s OR insight ILIKE %s
                          OR COALESCE(summary,'') ILIKE %s)
                   ORDER BY updated_at DESC LIMIT %s""",
                (identity, text, pattern, pattern, pattern, safe_limit),
            ).fetchall()
    except Exception as exc:
        raise KnowledgeUnavailable("knowledge_card_read_failed") from exc
    return [_row_card(row) for row in rows]


def update_card(
    identity_id: object,
    card_id: object,
    *,
    title: object,
    insight: object,
    summary: object = None,
) -> dict[str, object] | None:
    identity = _uuid(identity_id, "invalid_identity")
    card_id_value = _uuid(card_id, "invalid_card")
    validated = KnowledgeCardInput(
        title=str(title or ""),
        insight=str(insight or ""),
        summary=None if summary is None else str(summary),
    ).validated()
    try:
        with postgres_db.connect() as connection:
            row = connection.execute(
                """UPDATE oap_knowledge_cards
                   SET title=%s,insight=%s,summary=%s,updated_at=CURRENT_TIMESTAMP
                   WHERE owner_identity_id=%s AND card_id=%s AND deleted_at IS NULL
                   RETURNING card_id,title,insight,summary,evidence_state,visibility,
                             created_at,updated_at""",
                (
                    validated.title,
                    validated.insight,
                    validated.summary,
                    identity,
                    card_id_value,
                ),
            ).fetchone()
            if row is not None:
                connection.execute(
                    """INSERT INTO oap_knowledge_history(
                           owner_identity_id,card_id,action,from_visibility,to_visibility)
                       VALUES (%s,%s,'UPDATE','PRIVATE','PRIVATE')""",
                    (identity, card_id_value),
                )
            connection.commit()
    except (TypeError, ValueError):
        raise
    except Exception as exc:
        raise KnowledgeUnavailable("knowledge_card_update_failed") from exc
    return None if row is None else _row_card(row)


def delete_card(identity_id: object, card_id: object) -> bool:
    identity = _uuid(identity_id, "invalid_identity")
    card = _uuid(card_id, "invalid_card")
    try:
        with postgres_db.connect() as connection:
            row = connection.execute(
                """UPDATE oap_knowledge_cards
                   SET deleted_at=CURRENT_TIMESTAMP,updated_at=CURRENT_TIMESTAMP
                   WHERE owner_identity_id=%s AND card_id=%s AND deleted_at IS NULL
                   RETURNING card_id""",
                (identity, card),
            ).fetchone()
            if row is not None:
                connection.execute(
                    """INSERT INTO oap_knowledge_history(
                           owner_identity_id,card_id,action,from_visibility)
                       VALUES (%s,%s,'DELETE','PRIVATE')""",
                    (identity, card),
                )
            connection.commit()
    except Exception as exc:
        raise KnowledgeUnavailable("knowledge_card_delete_failed") from exc
    return row is not None


def create_collection(identity_id: object, *, title: object) -> dict[str, object]:
    identity = _uuid(identity_id, "invalid_identity")
    name = str(title or "").strip()
    if not name:
        raise ValueError("collection_title_required")
    if len(name) > 200:
        raise ValueError("collection_title_too_long")
    try:
        with postgres_db.connect() as connection:
            row = connection.execute(
                """INSERT INTO oap_knowledge_collections(owner_identity_id,title,visibility)
                   VALUES (%s,%s,'PRIVATE')
                   RETURNING collection_id,title,visibility,created_at,updated_at""",
                (identity, name),
            ).fetchone()
            connection.commit()
    except (TypeError, ValueError):
        raise
    except Exception as exc:
        raise KnowledgeUnavailable("knowledge_collection_write_failed") from exc
    if row is None:
        raise KnowledgeUnavailable("knowledge_collection_write_failed")
    created_at = row[3].isoformat() if hasattr(row[3], "isoformat") else str(row[3])
    updated_at = row[4].isoformat() if hasattr(row[4], "isoformat") else str(row[4])
    return {
        "collection_id": str(row[0]),
        "title": str(row[1]),
        "visibility": str(row[2]),
        "created_at": created_at,
        "updated_at": updated_at,
    }


def add_card_to_collection(
    identity_id: object,
    collection_id: object,
    card_id: object,
) -> bool:
    identity = _uuid(identity_id, "invalid_identity")
    collection = _uuid(collection_id, "invalid_collection")
    card = _uuid(card_id, "invalid_card")
    try:
        with postgres_db.connect() as connection:
            owned = connection.execute(
                """SELECT 1
                   FROM oap_knowledge_collections c
                   JOIN oap_knowledge_cards k
                     ON k.card_id=%s AND k.owner_identity_id=%s
                    AND k.deleted_at IS NULL
                   WHERE c.collection_id=%s AND c.owner_identity_id=%s""",
                (card, identity, collection, identity),
            ).fetchone()
            if owned is None:
                return False
            position_row = connection.execute(
                """SELECT COALESCE(MAX(position),0)+1
                   FROM oap_knowledge_collection_items
                   WHERE collection_id=%s""",
                (collection,),
            ).fetchone()
            position = int(position_row[0]) if position_row else 1
            connection.execute(
                """INSERT INTO oap_knowledge_collection_items(
                       collection_id,card_id,position)
                   VALUES (%s,%s,%s)
                   ON CONFLICT (collection_id,card_id) DO NOTHING""",
                (collection, card, position),
            )
            connection.commit()
    except Exception as exc:
        raise KnowledgeUnavailable("knowledge_collection_link_failed") from exc
    return True
