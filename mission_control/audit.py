"""Mission Control adapter for the canonical OAP audit chain."""

from __future__ import annotations

from oap.audit import append_event, verify_audit_path

from . import config

__all__ = ["append_event", "verify_audit"]


def verify_audit(db_path: str | None = None) -> tuple[bool, list[str]]:
    return verify_audit_path(db_path or config.OAP_DATABASE_PATH)
