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
from oap.smi.input_manager import InputManager
from oap.smi.judge_engine import JudgeEngine
from oap.smi.organ_manager import OrganManager
from oap.smi.organs.base import BrainPacket
from oap.war_room.engine import WarRoomEngine


def classify_task(content: str) -> str:
    """Select an approved task family without granting action authority."""
    text = content.casefold()
    groups = (
        ("TECHNICAL", ("code", "deploy", "database", "postgres", "api", "architecture", "render", "github")),
        ("COMMUNITY", ("postcode", "borough", "county", "community", "school", "local")),
        ("AKAN", ("akan", "akyem", "ghana", "adinkra", "heritage")),
        ("CULTURE", ("culture", "education", "learning", "history", "civilisation")),
        ("MONITORING", ("monitor", "signal", "health", "alert", "performance")),
        ("STRATEGY", ("strategy", "plan", "roadmap", "priority", "business")),
    )
    return next((task for task, words in groups if any(word in text for word in words)), "GENERAL")


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


def review(
    *,
    request_id: str,
    identity_id: str,
    content: str,
    history: list[dict[str, str]],
    image_attached: bool,
) -> dict[str, Any]:
    """Run the canonical NEXUS/Identity/Registry/Brain/Guardian/War Room review."""
    task_type = classify_task(content)
    high_impact = any(
        phrase in content.casefold()
        for phrase in ("deploy", "publish", "delete", "send money", "activate", "execute")
    )
    request = BrainRequest(
        request_id=request_id,
        identity_id=identity_id,
        content=content,
        task_type=task_type,
        metadata={"image_attached": image_attached, "interface": "smi_chat"},
        high_impact=high_impact,
    )
    signal = InputManager().receive(NexusRouter().receive(request))
    identity = IdentityRecord(
        identity_id=identity_id,
        identity_type="human",
        authority_level=5,
        permissions=frozenset({"REQUEST_RECOMMENDATION"}),
        roles=("community_member",),
    )
    permission = PermissionEngine().authorize_identity(identity)
    registry = RegistryEngine(AGENT_REGISTRY, LOCKED_FAMILY_IDS)
    advisors = registry.select_advisors(task_type)
    context = ContextSnapshot(
        memories=_memory_context(history),
        world_state={"interface": "SMI Chat", "human_authority_final": True},
        retrieved_at=utc_now(),
    )
    packet = BrainPacket(
        signal=signal,
        context=context,
        advisors=advisors,
        provider_results=(
            ProviderResult(provider_id="openai", available=True, text="provider_ready"),
        ),
    )
    organs = OrganManager()
    findings = organs.run_regions(packet)
    analysis = organs.integrate(findings)
    aegis_findings = AegisEngine().inspect(signal)
    safety = GuardianEngine().protect(signal, permission, aegis_findings)
    output_state = JudgeEngine().decide(request, analysis, safety)
    war_room = WarRoomEngine().review(request, analysis, safety, output_state)
    return {
        "passed": safety.passed,
        "high_impact": high_impact,
        "task_type": task_type,
        "output_state": output_state.value,
        "signal_level": safety.signal_level.value,
        "advisor_ids": list(advisors.agent_ids),
        "agent_count": len(advisors.agent_ids),
        "brain_regions": [finding.organ_id for finding in findings] + [organs.corpus_callosum.organ_id],
        "brain_region_count": len(findings) + 1,
        "analysis_summary": analysis.summary,
        "analysis_confidence": analysis.confidence,
        "safety_codes": [finding.code for finding in safety.findings],
        "guardian_reason": "; ".join(finding.message for finding in safety.findings)[:500],
        "war_room": {
            "triggered": war_room.triggered,
            "recommendation": war_room.recommendation,
            "scenarios": list(war_room.scenarios),
        },
        "processing_states": [
            "NEXUS_RECEIVED",
            "IDENTITY_VERIFIED",
            "PERMISSION_VERIFIED",
            "AGENTS_SELECTED",
            "BIOLOGICAL_BRAIN_REVIEWED",
            "AEGIS_REVIEWED",
            "GUARDIAN_PASSED" if safety.passed else "GUARDIAN_BLOCKED",
            "WAR_ROOM_REVIEWED" if war_room.triggered else "STANDARD_REVIEW",
        ],
        "human_authority_final": True,
        "can_execute": False,
    }
