"""Canonical governed brain review for the live Sovereign Megaverse Intelligence UI."""

from __future__ import annotations

from typing import Any

from mission_control.agents import AGENT_REGISTRY, LOCKED_FAMILY_IDS
from oap.aegis.engine import AegisEngine
from oap.contracts import (
    BrainRequest,
    ContextSnapshot,
    IdentityRecord,
    MemoryItem,
    OutputState,
    ProviderResult,
    utc_now,
)
from oap.guardian.engine import GuardianEngine
from oap.nexus.router import NexusRouter
from oap.permissions.engine import PermissionEngine
from oap.registry.engine import RegistryEngine
from oap.smi.coherence import CoherenceEngine
from oap.smi.input_manager import InputManager
from oap.smi.judge_engine import JudgeEngine
from oap.smi.organ_manager import OrganManager
from oap.smi.organs.base import BrainPacket
from oap.smi.self_model import SelfModel
from oap.war_room.engine import WarRoomEngine

_HIGH_IMPACT_PHRASES = (
    "deploy",
    "publish",
    "delete",
    "send money",
    "transfer money",
    "payment",
    "withdraw",
    "activate",
    "execute",
    "production migration",
    "database migration",
    "change permission",
    "change role",
    "revoke access",
    "grant access",
    "external message",
    "driver dispatch",
    "book ride",
)


def classify_task(content: str) -> str:
    """Select an approved task family without granting action authority."""

    text = content.casefold()
    groups = (
        (
            "TECHNICAL",
            (
                "code",
                "deploy",
                "database",
                "postgres",
                "api",
                "architecture",
                "render",
                "github",
            ),
        ),
        (
            "COMMUNITY",
            ("postcode", "borough", "county", "community", "school", "local"),
        ),
        ("AKAN", ("akan", "akyem", "ghana", "adinkra", "heritage")),
        (
            "CULTURE",
            ("culture", "education", "learning", "history", "civilisation"),
        ),
        (
            "MONITORING",
            ("monitor", "signal", "health", "alert", "performance"),
        ),
        ("STRATEGY", ("strategy", "plan", "roadmap", "priority", "business")),
    )
    return next(
        (task for task, words in groups if any(word in text for word in words)),
        "GENERAL",
    )


def _is_high_impact(content: str) -> bool:
    text = content.casefold()
    return any(phrase in text for phrase in _HIGH_IMPACT_PHRASES)


def _memory_context(history: list[dict[str, str]]) -> tuple[MemoryItem, ...]:
    items: list[MemoryItem] = []
    for index, item in enumerate(history[-5:]):
        if item.get("role") != "assistant":
            continue
        summary = str(item.get("content", "")).strip()[:600]
        if summary:
            items.append(
                MemoryItem(
                    memory_id=f"conversation-{index}",
                    task_type="GENERAL",
                    summary=summary,
                    output_state=OutputState.RECOMMENDATION_READY.value,
                    created_at=utc_now(),
                )
            )
    return tuple(items)


def _identity_from_authority_context(
    identity_id: str,
    authority_context: dict[str, object] | None,
) -> tuple[IdentityRecord, bool]:
    record = authority_context or {}
    try:
        authority_level = int(record.get("authority_level", 5))
    except (TypeError, ValueError):
        authority_level = 5

    raw_permissions = record.get("permissions")
    if isinstance(raw_permissions, (tuple, list, set, frozenset)):
        permissions = frozenset(str(item) for item in raw_permissions)
    else:
        permissions = frozenset({"REQUEST_RECOMMENDATION"})

    is_human_authority = bool(record.get("is_human_authority")) and (
        authority_level == 0 and "APPROVE_RECOMMENDATION" in permissions
    )
    roles = (
        ("human_authority", "community_member")
        if is_human_authority
        else ("community_member",)
    )
    identity = IdentityRecord(
        identity_id=identity_id,
        identity_type="HUMAN_AUTHORITY" if is_human_authority else "HUMAN",
        authority_level=authority_level,
        permissions=permissions,
        roles=roles,
    )
    return identity, is_human_authority


def review(
    *,
    request_id: str,
    identity_id: str,
    content: str,
    history: list[dict[str, str]],
    image_attached: bool,
    authority_context: dict[str, object] | None = None,
) -> dict[str, Any]:
    """Run the canonical NEXUS/Identity/Registry/Brain/Guardian/War Room review."""

    task_type = classify_task(content)
    high_impact = _is_high_impact(content)
    request = BrainRequest(
        request_id=request_id,
        identity_id=identity_id,
        content=content,
        task_type=task_type,
        metadata={"image_attached": image_attached, "interface": "smi_chat"},
        high_impact=high_impact,
    )
    signal = InputManager().receive(NexusRouter().receive(request))
    identity, is_human_authority = _identity_from_authority_context(
        identity_id,
        authority_context,
    )
    permission = PermissionEngine().authorize_identity(identity)
    registry = RegistryEngine(AGENT_REGISTRY, LOCKED_FAMILY_IDS)
    advisors = registry.select_advisors(task_type)
    context = ContextSnapshot(
        memories=_memory_context(history),
        world_state={
            "interface": "SMI Chat",
            "human_authority_final": True,
            "authority_level": identity.authority_level,
            "is_human_authority": is_human_authority,
        },
        retrieved_at=utc_now(),
    )
    provider_results = (
        ProviderResult(provider_id="openai", available=True, text="provider_ready"),
    )
    packet = BrainPacket(
        signal=signal,
        context=context,
        advisors=advisors,
        provider_results=provider_results,
    )
    organs = OrganManager()
    findings = organs.run_regions(packet)
    analysis = organs.integrate(findings)
    aegis = AegisEngine()
    guardian = GuardianEngine()
    war_room_engine = WarRoomEngine()
    aegis_findings = aegis.inspect(signal)
    safety = guardian.protect(signal, permission, aegis_findings)
    output_state = JudgeEngine().decide(request, analysis, safety)

    components = (
        registry.status(),
        organs.status(),
        aegis.status(),
        guardian.status(),
        war_room_engine.status(),
        {
            "component": "Live Provider Fabric",
            "ready": all(result.available for result in provider_results),
            "mode": "approved_route",
        },
    )
    self_model = SelfModel().observe(components)
    coherence = CoherenceEngine().evaluate(components)
    if (
        (not self_model.overall_ready or not coherence.coherent)
        and output_state != OutputState.BLOCK_REQUEST
    ):
        output_state = OutputState.REVIEW_REQUIRED

    war_room = war_room_engine.review(
        request,
        analysis,
        safety,
        output_state,
        advisor_ids=advisors.agent_ids,
        provider_results=provider_results,
        authority_level=identity.authority_level,
        authority_roles=identity.roles,
        self_model=self_model.as_dict(),
        coherence=coherence.as_dict(),
    )
    return {
        "passed": safety.passed,
        "high_impact": high_impact,
        "task_type": task_type,
        "output_state": output_state.value,
        "signal_level": safety.signal_level.value,
        "advisor_ids": list(advisors.agent_ids),
        "agent_count": len(advisors.agent_ids),
        "brain_regions": [finding.organ_id for finding in findings]
        + [organs.corpus_callosum.organ_id],
        "brain_region_count": len(findings) + 1,
        "analysis_summary": analysis.summary,
        "analysis_confidence": analysis.confidence,
        "safety_codes": [finding.code for finding in safety.findings],
        "guardian_reason": "; ".join(
            finding.message for finding in safety.findings
        )[:500],
        "authority": {
            "authority_level": identity.authority_level,
            "roles": list(identity.roles),
            "is_human_authority": is_human_authority,
        },
        "self_model": self_model.as_dict(),
        "operational_coherence": coherence.as_dict(),
        "war_room": {
            "triggered": war_room.triggered,
            "recommendation": war_room.recommendation,
            "scenarios": list(war_room.scenarios),
            "evidence": list(war_room.evidence),
            "participants": list(war_room.participants),
            "positions": list(war_room.positions),
            "dissent": list(war_room.dissent),
            "authority_level": war_room.authority_level,
            "coherence_conflicts": list(war_room.coherence_conflicts),
            "reversibility_required": war_room.reversibility_required,
            "decision_authority": False,
        },
        "processing_states": [
            "NEXUS_RECEIVED",
            "IDENTITY_VERIFIED",
            "PERMISSION_VERIFIED",
            "AGENTS_SELECTED",
            "BIOLOGICAL_BRAIN_REVIEWED",
            "AEGIS_REVIEWED",
            "GUARDIAN_PASSED" if safety.passed else "GUARDIAN_BLOCKED",
            "SELF_MODEL_REVIEWED",
            "COHERENCE_REVIEWED",
            "WAR_ROOM_REVIEWED" if war_room.triggered else "STANDARD_REVIEW",
        ],
        "human_authority_final": True,
        "can_execute": False,
    }
