"""Create SMI-owned HRM, approval, Kernel outcome and world-state tables."""

from __future__ import annotations

from oap.hrm.schema import initialize_brain_schema


def migrate(connection):
    """Run inside the transaction owned by the migration runner."""

    initialize_brain_schema(connection)
