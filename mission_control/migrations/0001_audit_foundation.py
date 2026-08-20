"""Create the canonical append-only OAP audit foundation."""

from __future__ import annotations

from oap.audit.schema import initialize_audit_schema


def migrate(connection):
    """Run inside the transaction owned by the migration runner."""

    initialize_audit_schema(connection)
