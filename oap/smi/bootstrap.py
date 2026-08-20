"""Explicit dependency wiring for the SMI Brain runtime."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable, Mapping

from mission_control.agents import (
    AGENT_REGISTRY,
    LOCKED_FAMILY_IDS,
    validate_agent_registry,
)
from oap.aegis import AegisEngine
from oap.contracts import IdentityRecord
from oap.guardian import GuardianEngine
from oap.hrm import HRMCore
from oap.identity import IdentityEngine
from oap.nexus import NexusRouter
from oap.permissions import PermissionEngine
from oap.registry import RegistryEngine
from oap.war_room import WarRoomEngine
from oap.world import WorldEngine

from .context_engine import ContextEngine
from .judge_engine import JudgeEngine
from .organ_manager import OrganManager
from .providers import ProviderAdapter, ProviderRouter
from .smi_core import SMICore


def build_smi(
    connection: sqlite3.Connection,
    *,
    identities: Iterable[IdentityRecord] = (),
    provider_adapters: tuple[ProviderAdapter, ...] = (),
    approved_provider_assignments: Mapping[str, str] | None = None,
) -> SMICore:
    """Build one SMI instance; the caller must initialize storage explicitly."""

    registry_validation = validate_agent_registry()
    if not registry_validation["passed"]:
        raise RuntimeError("Approved Agent Registry validation failed")
    hrm = HRMCore(connection)
    world = WorldEngine(connection)
    return SMICore(
        nexus=NexusRouter(),
        identity=IdentityEngine(identities),
        permissions=PermissionEngine(),
        context=ContextEngine(hrm, world),
        registry=RegistryEngine(AGENT_REGISTRY, LOCKED_FAMILY_IDS),
        providers=ProviderRouter(
            adapters=provider_adapters,
            approved_assignments=approved_provider_assignments,
        ),
        organs=OrganManager(),
        aegis=AegisEngine(),
        guardian=GuardianEngine(),
        judge=JudgeEngine(),
        war_room=WarRoomEngine(),
        hrm=hrm,
    )
