"""Explicit first-party Everyday SQLite records sharing canonical OAP audit.

No import-time migration. Schema creation requires an existing canonical audit
schema on the same supplied connection. No public listing or entry routes.
"""
from __future__ import annotations

import sqlite3
from datetime import date, datetime, timezone
from urllib.parse import urlsplit

from oap.audit import append_event, audit_schema_ready

SCHEMA = (
    ("CREATE TABLE IF NOT EXISTS everyday_partners ("
    "id TEXT PRIMARY KEY, organisation TEXT NOT NULL, prize TEXT NOT NULL,"
    "status TEXT NOT NULL CHECK(status='proposed'),"
    "sponsor_confirmed INTEGER NOT NULL DEFAULT 0 CHECK(sponsor_confirmed=0),"
    "prize_secured INTEGER NOT NULL DEFAULT 0 CHECK(prize_secured=0))"),
    ("CREATE TABLE IF NOT EXISTS everyday_resources ("
    "id TEXT PRIMARY KEY, title TEXT NOT NULL, url TEXT NOT NULL,"
    "source_name TEXT NOT NULL, checked_on TEXT NOT NULL,"
    "status TEXT NOT NULL CHECK(status='private_review'))"),
)


def initialize_schema(connection: sqlite3.Connection) -> None:
    if not audit_schema_ready(connection):
        raise RuntimeError("canonical_audit_schema_required")
    for statement in SCHEMA:
        connection.execute(statement)


def _transaction(connection: sqlite3.Connection, work):
    if connection.in_transaction:
        raise RuntimeError("exclusive_everyday_transaction_required")
    connection.execute("BEGIN IMMEDIATE")
    try:
        result = work()
        connection.commit()
        return result
    except Exception:
        connection.rollback()
        raise


def propose_partner(connection: sqlite3.Connection, *, record_id: str,
                    organisation: str, prize: str, actor: str) -> dict[str, object]:
    from oap.everyday import propose_partner as validate

    result = validate(organisation=organisation, prize_description=prize)
    if not record_id or len(record_id) > 96 or not actor:
        raise ValueError("record_and_actor_required")

    def work():
        connection.execute(
            "INSERT INTO everyday_partners(id,organisation,prize,status) "
            "VALUES(?,?,?,'proposed')",
            (record_id, result["organisation"], result["prize_description"]))
        receipt = append_event(connection, actor, "HUMAN", None,
                               "EVERYDAY_PARTNER_PROPOSED", record_id,
                               "PRIVATE_UNVERIFIED", {"status": "proposed"})
        if not isinstance(receipt, tuple) or len(receipt) != 2:
            raise RuntimeError("canonical_audit_unconfirmed")
        return {"id": record_id, "status": "proposed_unverified",
                "prize_secured": False, "receipt_seq": receipt[0]}
    return _transaction(connection, work)


def propose_resource(connection: sqlite3.Connection, *, record_id: str,
                     title: str, url: str, source: str, checked_on: str,
                     actor: str) -> dict[str, object]:
    parts = urlsplit(url)
    if (not record_id or len(record_id) > 96 or not actor
        or not isinstance(title, str) or not title.strip() or len(title) > 160
        or not isinstance(source, str) or not source.strip() or len(source) > 160
        or parts.scheme != "https" or not parts.hostname
        or parts.username or parts.password or len(url) > 800):
        raise ValueError("invalid_private_resource")
    try:
        reviewed = date.fromisoformat(checked_on)
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid_review_date") from exc
    if reviewed > datetime.now(timezone.utc).date():
        raise ValueError("future_review_date")

    def work():
        connection.execute(
            "INSERT INTO everyday_resources(id,title,url,source_name,checked_on,status) "
            "VALUES(?,?,?,?,?,'private_review')",
            (record_id, title.strip(), url, source.strip(), checked_on))
        receipt = append_event(connection, actor, "HUMAN", None,
                               "EVERYDAY_RESOURCE_PROPOSED", record_id,
                               "PRIVATE_REVIEW_ONLY", {"checked_on": checked_on})
        if not isinstance(receipt, tuple) or len(receipt) != 2:
            raise RuntimeError("canonical_audit_unconfirmed")
        return {"id": record_id, "status": "private_review",
                "published": False, "receipt_seq": receipt[0]}
    return _transaction(connection, work)


def records(connection: sqlite3.Connection) -> dict[str, object]:
    if not audit_schema_ready(connection):
        raise RuntimeError("canonical_audit_schema_required")
    partners = connection.execute(
        "SELECT id,organisation,prize,status FROM everyday_partners ORDER BY id"
    ).fetchall()
    resources = connection.execute(
        "SELECT id,title,url,source_name,checked_on,status "
        "FROM everyday_resources ORDER BY id"
    ).fetchall()
    return {
        "partners": [dict(zip(("id","organisation","prize","status"), row))
                     for row in partners],
        "resources": [dict(zip(("id","title","url","source","checked_on","status"), row))
                      for row in resources],
        "public_listing_allowed": False,
        "entries_open": False, "payments_enabled": False,
    }
