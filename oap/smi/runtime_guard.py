"""Deterministic runtime controls for bounded SMI work.

These guards do not grant execution authority. They reject authority growth,
runaway work, duplicate work, and unsafe payload shapes before a Builder path.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

PROTECTED_KEYS = frozenset({
    "authority", "authority_level", "permissions", "permission", "roles", "role",
    "founder_identity", "guardian_authority", "aegis_authority",
    "green_gate_authority", "war_room_authority", "deployment_authority",
    "constitution", "security_boundaries", "agent_registry",
})

MAX_DEPTH = 12
MAX_COLLECTION_ITEMS = 256
MAX_RETRIES = 3
MAX_CHAIN_DEPTH = 21
MAX_REQUESTS_PER_CHAIN = 64


class RuntimeGuardViolation(PermissionError):
    """Raised when bounded SMI work attempts to cross a protected boundary."""


def _walk(value: Any, *, depth: int = 0) -> None:
    if depth > MAX_DEPTH:
        raise RuntimeGuardViolation("payload_nesting_limit_exceeded")
    if isinstance(value, Mapping):
        if len(value) > MAX_COLLECTION_ITEMS:
            raise RuntimeGuardViolation("payload_collection_limit_exceeded")
        for key, item in value.items():
            normalized = str(key).strip().casefold()
            if normalized in PROTECTED_KEYS:
                raise RuntimeGuardViolation(f"protected_key_blocked:{normalized}")
            _walk(item, depth=depth + 1)
    elif isinstance(value, (list, tuple, set, frozenset)):
        if len(value) > MAX_COLLECTION_ITEMS:
            raise RuntimeGuardViolation("payload_collection_limit_exceeded")
        for item in value:
            _walk(item, depth=depth + 1)


def validate_action_payload(payload: Mapping[str, Any]) -> None:
    """Reject protected authority material and pathological payload structure."""

    _walk(payload)


def assert_no_authority_growth(
    before: Mapping[str, Any], after: Mapping[str, Any]
) -> None:
    """Fail closed when a proposal expands effective authority."""

    before_level = int(before.get("authority_level", 999))
    after_level = int(after.get("authority_level", 999))
    if after_level < before_level:
        raise RuntimeGuardViolation("authority_level_escalation_blocked")

    before_permissions = frozenset(str(x) for x in before.get("permissions", ()))
    after_permissions = frozenset(str(x) for x in after.get("permissions", ()))
    if not after_permissions.issubset(before_permissions):
        raise RuntimeGuardViolation("permission_expansion_blocked")


@dataclass
class WorkBudget:
    """Per-chain recursion, retry and duplicate-work guard."""

    chain_id: str
    max_depth: int = MAX_CHAIN_DEPTH
    max_retries: int = MAX_RETRIES
    max_requests: int = MAX_REQUESTS_PER_CHAIN
    requests: int = 0
    seen_keys: set[str] = field(default_factory=set)

    def admit(self, *, depth: int, retry: int, idempotency_key: str) -> None:
        if depth < 0 or depth > self.max_depth:
            raise RuntimeGuardViolation("recursion_depth_blocked")
        if retry < 0 or retry > self.max_retries:
            raise RuntimeGuardViolation("retry_budget_exceeded")
        key = idempotency_key.strip()
        if not key:
            raise RuntimeGuardViolation("idempotency_key_required")
        if key in self.seen_keys:
            raise RuntimeGuardViolation("duplicate_work_blocked")
        if self.requests >= self.max_requests:
            raise RuntimeGuardViolation("request_budget_exceeded")
        self.seen_keys.add(key)
        self.requests += 1


def bounded_control_proof() -> dict[str, bool]:
    """Exercise the controls without mutating product state."""

    budget = WorkBudget("proof")
    budget.admit(depth=1, retry=0, idempotency_key="proof-1")

    duplicate_blocked = False
    recursion_blocked = False
    retry_blocked = False
    escalation_blocked = False
    protected_payload_blocked = False

    try:
        budget.admit(depth=1, retry=0, idempotency_key="proof-1")
    except RuntimeGuardViolation:
        duplicate_blocked = True

    try:
        budget.admit(depth=MAX_CHAIN_DEPTH + 1, retry=0, idempotency_key="proof-2")
    except RuntimeGuardViolation:
        recursion_blocked = True

    try:
        budget.admit(depth=1, retry=MAX_RETRIES + 1, idempotency_key="proof-3")
    except RuntimeGuardViolation:
        retry_blocked = True

    try:
        assert_no_authority_growth(
            {"authority_level": 2, "permissions": ("read",)},
            {"authority_level": 1, "permissions": ("read", "deploy")},
        )
    except RuntimeGuardViolation:
        escalation_blocked = True

    try:
        validate_action_payload({"config": {"permissions": ["deploy"]}})
    except RuntimeGuardViolation:
        protected_payload_blocked = True

    passed = all((
        duplicate_blocked,
        recursion_blocked,
        retry_blocked,
        escalation_blocked,
        protected_payload_blocked,
    ))
    return {
        "duplicate_blocked": duplicate_blocked,
        "recursion_blocked": recursion_blocked,
        "retry_blocked": retry_blocked,
        "escalation_blocked": escalation_blocked,
        "protected_payload_blocked": protected_payload_blocked,
        "passed": passed,
        "production_state_mutated": False,
        "execution_authority_expanded": False,
        "human_authority_final": True,
    }
