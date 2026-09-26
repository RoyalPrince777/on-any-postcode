"""Canonical state ownership contracts for the single SMI brain.

This registry does not create another database, Intelligence World, agent family,
or execution authority. It declares which existing OAP component is allowed to
be authoritative for a state domain and makes conflicts fail closed for Human
Authority review.

A logical ownership contract is not proof that a production database binding or
migration is live. Runtime binding state is reported separately.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import Any

REVISION = "2026-09-26-v1"
_BINDING_STATES = {"contract_only", "runtime_proven"}


@dataclass(frozen=True, slots=True)
class StateOwner:
    domain_id: str
    owner_component: str
    canonical_entity: str
    store_class: str
    runtime_binding_state: str = "contract_only"
    consequential: bool = False

    def as_dict(self) -> dict[str, object]:
        return {
            "domain_id": self.domain_id,
            "owner_component": self.owner_component,
            "canonical_entity": self.canonical_entity,
            "store_class": self.store_class,
            "runtime_binding_state": self.runtime_binding_state,
            "consequential": self.consequential,
        }


_OWNERS: tuple[StateOwner, ...] = (
    StateOwner("identity", "identity", "users(id)", "canonical_application_store", consequential=True),
    StateOwner("world_place", "oap_world", "place/geography", "oap_world_store"),
    StateOwner("movement", "movement", "route/movement state", "movement_store"),
    StateOwner("arena_competition", "arena", "competition result", "arena_store"),
    StateOwner("arena_profile", "arena", "player profile/ranking", "canonical_application_store"),
    StateOwner("distribution", "distribution_intelligence", "distribution release/receipt", "distribution_store"),
    StateOwner("music_rights", "oap_music", "rights evidence/release", "music_store", consequential=True),
    StateOwner("commerce", "market", "merchant/order", "market_store", consequential=True),
    StateOwner("value", "sika", "SIKA ledger entry", "sika_canonical_ledger", consequential=True),
    StateOwner("organiser", "organiser", "schedule/notebook", "owner_scoped_workspace_store"),
    StateOwner("studio", "oap_studio", "build/workspace candidate", "owner_scoped_workspace_store"),
    StateOwner("intelligence_policy", "smi", "policy/capability state", "smi_control_state", consequential=True),
    StateOwner("audit_evidence", "oap_data", "evidence/audit receipt", "oap_data_evidence_store", consequential=True),
)

_BY_DOMAIN = {item.domain_id: item for item in _OWNERS}


def owners() -> tuple[StateOwner, ...]:
    return _OWNERS


def owner_for(domain_id: str) -> StateOwner | None:
    return _BY_DOMAIN.get(str(domain_id or "").strip().casefold())


def validate_registry() -> dict[str, Any]:
    ids = tuple(item.domain_id for item in _OWNERS)
    errors: list[str] = []
    if len(ids) != len(set(ids)):
        errors.append("Canonical state domains must be unique")
    for item in _OWNERS:
        if not item.owner_component.strip():
            errors.append(f"{item.domain_id}: owner component is required")
        if item.runtime_binding_state not in _BINDING_STATES:
            errors.append(f"{item.domain_id}: invalid runtime binding state")
    return {
        "passed": not errors,
        "errors": tuple(errors),
        "domain_count": len(_OWNERS),
        "unique_domains": len(ids) == len(set(ids)),
        "creates_database": False,
        "creates_brain": False,
        "creates_intelligence_world": False,
        "creates_agent_family": False,
        "silent_conflict_resolution": False,
        "human_authority_final": True,
    }


def assess_claims(statuses: Iterable[Mapping[str, object]]) -> dict[str, Any]:
    """Check component ownership claims against canonical owners."""
    conflicts: list[dict[str, object]] = []
    observed: dict[str, list[tuple[str, str]]] = {}

    for index, status in enumerate(tuple(statuses)):
        component = str(status.get("component") or f"unknown-{index + 1}")
        claims = status.get("state_ownership_claims")
        if not isinstance(claims, Mapping):
            continue
        for raw_domain, raw_owner in claims.items():
            domain = str(raw_domain).strip().casefold()
            claimed_owner = str(raw_owner).strip()
            observed.setdefault(domain, []).append((component, claimed_owner))
            expected = owner_for(domain)
            if expected is None:
                conflicts.append({
                    "domain_id": domain,
                    "reason": "unknown_state_domain",
                    "component": component,
                    "claimed_owner": claimed_owner,
                    "expected_owner": None,
                })
            elif claimed_owner != expected.owner_component:
                conflicts.append({
                    "domain_id": domain,
                    "reason": "owner_mismatch",
                    "component": component,
                    "claimed_owner": claimed_owner,
                    "expected_owner": expected.owner_component,
                })

    for domain, entries in observed.items():
        owners_seen = sorted({owner for _, owner in entries})
        if len(owners_seen) > 1:
            conflicts.append({
                "domain_id": domain,
                "reason": "competing_owner_claims",
                "components": tuple(component for component, _ in entries),
                "claimed_owners": tuple(owners_seen),
                "expected_owner": owner_for(domain).owner_component if owner_for(domain) else None,
            })

    return {
        "coherent": not conflicts,
        "human_review_required": bool(conflicts),
        "conflict_count": len(conflicts),
        "conflicts": tuple(conflicts),
        "checked_claim_domains": len(observed),
        "resolution": "coherent" if not conflicts else "human_review_required",
        "silent_resolution_performed": False,
    }


def status() -> dict[str, Any]:
    validation = validate_registry()
    runtime_proven = sum(item.runtime_binding_state == "runtime_proven" for item in _OWNERS)
    return {
        "component": "SMI Canonical State Ownership Registry",
        "revision": REVISION,
        "architecture_passed": validation["passed"],
        "validation": validation,
        "owners": tuple(item.as_dict() for item in _OWNERS),
        "domain_count": len(_OWNERS),
        "runtime_binding_proven_count": runtime_proven,
        "all_runtime_bindings_proven": runtime_proven == len(_OWNERS),
        "fail_closed_on_conflict": True,
        "human_authority_final": True,
        "truth_boundary": (
            "This registry defines logical state ownership only. It does not prove that "
            "every production database, migration, route or runtime binding is live."
        ),
    }
