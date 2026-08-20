"""OAP Permission Constitution v1.0 enforcement."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from oap.contracts import IdentityRecord, PermissionDecision


@dataclass(frozen=True, slots=True)
class AgentPermissionDecision:
    allowed: bool
    identity: str
    role: str | None
    family: str
    organ: str | None
    guardian: str
    memory: dict[str, Any]
    status: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


_RESTRICTION_ACTIONS = {
    "OVERRIDE_HUMAN_AUTHORITY": "Cannot override Human Authority",
    "SELF_APPROVE": "Cannot approve its own recommendation",
    "CHANGE_OWN_PERMISSIONS": "Cannot change its own permissions",
    "EXECUTE_FROM_INTERFACE": (
        "Cannot execute real-world actions from this interface"
    ),
}


class PermissionEngine:
    """Checks identity or agent permissions without granting new authority."""

    REQUEST_PERMISSION = "REQUEST_RECOMMENDATION"

    def authorize_identity(
        self,
        identity: IdentityRecord,
        required_permission: str = REQUEST_PERMISSION,
    ) -> PermissionDecision:
        if identity.status != "ACTIVE":
            return PermissionDecision(
                allowed=False,
                identity_id=identity.identity_id,
                authority_level=identity.authority_level,
                reason="Identity is not active",
                required_permission=required_permission,
                status=identity.status,
            )
        allowed = required_permission in identity.permissions
        return PermissionDecision(
            allowed=allowed,
            identity_id=identity.identity_id,
            authority_level=identity.authority_level,
            reason=(
                "Permission present"
                if allowed
                else f"Missing permission: {required_permission}"
            ),
            required_permission=required_permission,
            status=identity.status,
        )

    def authorize_agent(
        self,
        passport: dict[str, Any],
        required_permission: str,
        requested_action: str | None = None,
    ) -> AgentPermissionDecision:
        status = str(passport.get("status", "UNKNOWN"))
        permissions = set(passport.get("permissions", ()))
        restrictions = set(passport.get("restrictions", ()))
        reason = "Permission present"
        allowed = status == "ACTIVE" and required_permission in permissions

        if status != "ACTIVE":
            reason = "Agent status is not ACTIVE"
        elif required_permission not in permissions:
            reason = f"Missing permission: {required_permission}"
        elif requested_action:
            restriction = _RESTRICTION_ACTIONS.get(requested_action)
            if restriction and restriction in restrictions:
                allowed = False
                reason = restriction

        memory = passport.get("memory", {})
        if not passport.get("audit_required", memory.get("audit", False)):
            allowed = False
            reason = "Guardian audit flag is required"

        return AgentPermissionDecision(
            allowed=allowed,
            identity=str(passport.get("agent_id", "")),
            role=passport.get("role"),
            family=str(passport.get("family_id", "")),
            organ=passport.get("organ"),
            guardian=str(passport.get("guardian", "")),
            memory=dict(memory),
            status=status,
            reason=reason,
        )
