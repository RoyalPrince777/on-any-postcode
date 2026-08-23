"""Small cross-database helpers for OAP's SQLite/PostgreSQL foundation."""

from __future__ import annotations

from typing import Any


def is_postgres(connection: Any) -> bool:
    return connection.__class__.__module__.startswith("psycopg")


def execute(connection: Any, statement: str, parameters: tuple[Any, ...] = ()):
    if is_postgres(connection):
        statement = statement.replace("?", "%s")
    return connection.execute(statement, parameters)


def table_exists(connection: Any, table: str) -> bool:
    if is_postgres(connection):
        row = execute(
            connection,
            "SELECT 1 FROM information_schema.tables "
            "WHERE table_schema = current_schema() AND table_name = ? LIMIT 1",
            (table,),
        ).fetchone()
    else:
        row = execute(
            connection,
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ? LIMIT 1",
            (table,),
        ).fetchone()
    return row is not None


def table_columns(connection: Any, table: str) -> set[str]:
    if not table_exists(connection, table):
        return set()
    if is_postgres(connection):
        rows = execute(
            connection,
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_schema = current_schema() AND table_name = ?",
            (table,),
        ).fetchall()
        return {str(row[0]) for row in rows}
    return {
        str(row[1])
        for row in execute(connection, f"PRAGMA table_info({table})").fetchall()
    }


def integrity_ready(connection: Any) -> bool:
    if is_postgres(connection):
        row = execute(connection, "SELECT 1 AS ready").fetchone()
        return row is not None and int(row["ready"] if isinstance(row, dict) else row[0]) == 1
    row = execute(connection, "PRAGMA integrity_check").fetchone()
    return row is not None and row[0] == "ok"
