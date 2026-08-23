"""Health check system for production monitoring."""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class HealthStatus(str, Enum):
    """Overall health status."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class HealthCheck:
    """Multi-component health check system."""

    def __init__(self, container: Any):
        self.container = container

    def check(self) -> dict[str, Any]:
        """Run all health checks and return overall status."""
        now = datetime.now(timezone.utc).isoformat()

        checks = {
            "database": self._check_database(),
            "audit_chain": self._check_audit_chain(),
            "approval_security": self._check_approval_security(),
            "registry": self._check_registry(),
        }

        all_ok = all(check.get("ok", False) for check in checks.values())
        overall_status = HealthStatus.HEALTHY if all_ok else HealthStatus.DEGRADED

        result = {
            "timestamp": now,
            "status": overall_status.value,
            "checks": checks,
        }

        logger.info(
            f"Health check: {overall_status.value}",
            extra={"checks": checks},
        )

        return result

    def _check_database(self) -> dict[str, Any]:
        """Check database connectivity."""
        try:
            result = self.container.database.fetch_one("SELECT 1")
            return {
                "ok": result is not None,
                "message": "Database connection OK",
                "component": "database",
            }
        except Exception as exc:  # noqa: BLE001 - health boundary must degrade.
            logger.error("Database health check failed: %s", exc)
            return {
                "ok": False,
                "message": f"Database error: {exc!s}",
                "component": "database",
            }

    def _check_audit_chain(self) -> dict[str, Any]:
        """Verify audit chain integrity."""
        try:
            verification = self.container.audit.verify_chain()
            return {
                "ok": verification["valid"],
                "message": f"Audit chain: {verification['checked']} events verified",
                "component": "audit_chain",
                "events_checked": verification["checked"],
            }
        except Exception as exc:  # noqa: BLE001 - health boundary must degrade.
            logger.error("Audit chain health check failed: %s", exc)
            return {
                "ok": False,
                "message": f"Audit chain error: {exc!s}",
                "component": "audit_chain",
            }

    def _check_approval_security(self) -> dict[str, Any]:
        """Check approval security configuration."""
        ready = self.container.settings.approval_ready
        return {
            "ok": ready,
            "message": (
                "Approval security configured"
                if ready
                else "WARNING: Approval security NOT configured"
            ),
            "component": "approval_security",
        }

    def _check_registry(self) -> dict[str, Any]:
        """Validate agent registry integrity."""
        try:
            validation = self.container.registry.validate()
            return {
                "ok": validation["valid"],
                "message": f"Registry: {validation['count']} agents valid",
                "component": "registry",
                "agent_count": validation["count"],
            }
        except Exception as exc:  # noqa: BLE001 - health boundary must degrade.
            logger.error("Registry health check failed: %s", exc)
            return {
                "ok": False,
                "message": f"Registry error: {exc!s}",
                "component": "registry",
            }
