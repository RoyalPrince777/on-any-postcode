"""Founder-only, read-only Hybrid Agents HQ rooms and canonical home placement.

Every registered agent keeps one canonical family, intelligence world and home
system. Matrix film-home references are advisory provenance, never new agents.
Collaboration never transfers an agent's identity or grants execution.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from itertools import pairwise
from typing import Any

from . import agents, ai_behaviour_protocol


def _family_index() -> dict[str, Mapping[str, Any]]:
    families: dict[str, Mapping[str, Any]] = {}
    for family in agents.INTELLIGENCE_FAMILIES:
        family_id = str(family.get("id") or "")
        if not family_id or family_id in families:
            raise ValueError("Invalid or duplicate canonical family")
        if not all(str(family.get(key) or "").strip() for key in ("name", "world_id", "home_system")):
            raise ValueError("Canonical family missing home alignment")
        families[family_id] = family
    return families


def _home_profile(
    agent: Mapping[str, Any], families: Mapping[str, Mapping[str, Any]]
) -> dict[str, Any]:
    family_id = str(agent.get("family_id") or "")
    if family_id not in families:
        raise ValueError("Agent has no registered canonical family")
    family = families[family_id]
    film_home = None
    # Newer canonical agent registries include distinct Matrix film-home groups.
    # Reuse the canonical resolver when present; never duplicate its group roster.
    resolver = getattr(agents, "matrix_home_for", None)
    if family_id == "matrix" and callable(resolver):
        film_home = resolver(str(agent.get("name") or ""))
        if film_home is not None and film_home.get("family_id") != "matrix":
            raise ValueError("Matrix home reference has mismatched family")
    return {
        "family_id": family_id,
        "family_name": str(family["name"]),
        "world_id": str(family["world_id"]),
        "home_system": str(family["home_system"]),
        "home_group": film_home,
    }


def room_directory() -> dict[str, Any]:
    """Project all agents, individual rooms and their original family homes."""
    registry = agents.AGENT_REGISTRY
    ids = [str(agent["agent_id"]) for agent in registry]
    if any(not agent_id for agent_id in ids) or len(ids) != len(set(ids)):
        raise ValueError("Invalid or duplicate canonical agent passport")
    families = _family_index()
    profiles = {agent_id: _home_profile(agent, families)
                for agent_id, agent in zip(ids, registry)}
    rooms: list[dict[str, Any]] = [
        {
            "id": "all_agents",
            "kind": "all_agents",
            "name": "All Agents",
            "agent_ids": tuple(ids),
            "home_system": None,
            "world_id": None,
        }
    ]
    rooms.extend(
        {
            "id": f"agent:{agent_id}",
            "kind": "individual",
            "name": str(agent["name"]),
            "agent_ids": (agent_id,),
            **profiles[agent_id],
        }
        for agent_id, agent in zip(ids, registry)
    )
    for family_id, family in families.items():
        members = tuple(
            agent_id for agent_id in ids if profiles[agent_id]["family_id"] == family_id
        )
        rooms.append(
            {
                "id": f"family:{family_id}",
                "kind": "family",
                "name": str(family["name"]),
                "agent_ids": members,
                "family_id": family_id,
                "family_name": str(family["name"]),
                "world_id": str(family["world_id"]),
                "home_system": str(family["home_system"]),
            }
        )
    return {
        "scope": "founder_only",
        "mode": "read_only_room_directory",
        "source": "canonical_agent_registry",
        "home_assignment_source": "canonical_family_alignment",
        "human_authority": "Founder Final",
        "agent_count": len(ids),
        "rooms": tuple(rooms),
        "messages": (),
        "message_history_available": False,
        "autonomous_agent_chat": False,
        "cross_family_collaboration_active": False,
        "permissions_changed": False,
        "can_execute": False,
    }


def room_context(room_id: str) -> dict[str, Any]:
    """Return registered members and their original homes, never a second roster."""
    if not isinstance(room_id, str) or not room_id.strip():
        raise ValueError("Room ID required")
    directory = room_directory()
    room = next((item for item in directory["rooms"] if item["id"] == room_id), None)
    if room is None:
        raise ValueError("Unknown canonical room")
    families = _family_index()
    by_id: dict[str, Mapping[str, Any]] = {
        str(agent["agent_id"]): agent for agent in agents.AGENT_REGISTRY
    }
    return {
        "room": room,
        "members": tuple(
            {
                "agent_id": agent_id,
                "name": str(by_id[agent_id]["name"]),
                **_home_profile(by_id[agent_id], families),
            }
            for agent_id in room["agent_ids"]
        ),
        "mode": "read_only_context",
        "actual_messages": (),
        "agent_responses_generated": False,
        "founder_final": True,
        "can_execute": False,
    }


# Advisory skill requirements for existing SMI behaviour steps, not new agent skills.
# No evidence of deployed ability or runtime availability is inferred from passports.
_STEP_SKILL_TERMS: dict[str, tuple[str, ...]] = {
    "watch": ("monitoring", "observation", "signals", "surveillance"),
    "strip_noise": ("analysis", "pattern", "duplicate", "integrity"),
    "classify": ("analysis", "assessment", "classification", "risk"),
    "select_intelligence": ("strategy", "systems", "coordination"),
    "select_agent": ("coordination", "strategy", "leadership"),
    "select_protocol": ("architecture", "systems", "planning"),
    "helper_agents": ("collaboration", "coordination", "communication"),
    "no_bypass": ("security", "protection", "integrity", "risk"),
    "visible_reasoning_only": ("communication", "explanation", "analysis"),
    "score": ("evaluation", "analysis", "performance", "assessment"),
    "recover": ("recovery", "resilience", "repair", "restoration"),
    "offline_or_terminate_task": ("safety", "security", "protection", "risk"),
    "learn": ("learning", "memory", "knowledge", "research"),
}
_AUTHORITY_GATES = ("Guardian", "Green Gate", "HRM", "Founder Final")

# Seven-round council is a review *template*. It contains no generated
# conversation, agent ballots, independent approvals, or awarded stars.
_COUNCIL_ROUNDS = (
    ("brainstorm", "Brainstorm", "proposal_and_alternatives"),
    ("challenge", "Adversarial challenge", "risks_and_counterarguments"),
    ("defend", "Evidence-backed defence", "sources_and_test_receipts"),
    ("counter_challenge", "Alternatives and protection", "reversible_options"),
    ("guardian", "Guardian boundary review", "security_and_authority_proof"),
    ("green_gate", "HRM and Green Gate proof", "attributable_runtime_evidence"),
    ("council", "Council recommendation", "authenticated_positions_and_dissent"),
)


def _council_review_template() -> dict[str, Any]:
    rounds = tuple({
        "round": index,
        "id": round_id,
        "label": label,
        "required_evidence": required,
        "status": "not_conducted",
        "authenticated_speakers": (),
        "agent_statements": (),
        "votes": (),
        "minority_report": None,
        "earned_stars": None,
    } for index, (round_id, label, required) in enumerate(_COUNCIL_ROUNDS, 1))
    return {
        "mode": "council_review_template_only",
        "rounds": rounds,
        "rounds_completed": 0,
        "authenticated_ballots": 0,
        "votes_are_binding": False,
        "council_recommendation": None,
        "earned_stars": None,
        "hrm_receipt": None,
        "guardian_passed": False,
        "founder_final": True,
        "can_execute": False,
    }



# Candidate automation triggers are evidence-review suggestions, not jobs.
# Scheduling, event subscriptions, execution and delivery remain disabled.
_AUTOMATION_PATTERNS = (
    ("schedule", ("daily", "weekly", "hourly", "every morning", "each week", "scheduled", "recurring")),
    ("event", ("when ", "whenever ", "on failure", "on change", "on update", "on merge")),
    ("recovery", ("recover", "rollback", "outage", "failure", "retry", "incident")),
)


def _automation_review_template(mission: str) -> dict[str, Any]:
    text = mission.casefold()
    candidates = tuple({
        "trigger_kind": kind,
        "selection_basis": "mission_keyword_advisory_only",
        "state": "not_configured",
        "schedule": None,
        "event_source": None,
        "registered_job_id": None,
        "sender_verified": False,
        "guardian_passed": False,
        "hrm_receipt": None,
        "executions": 0,
    } for kind, words in _AUTOMATION_PATTERNS if any(word in text for word in words))
    return {
        "mode": "automation_advisory_only",
        "trigger_candidates": candidates,
        "jobs_created": 0,
        "jobs_enabled": 0,
        "notifications_sent": 0,
        "scheduler_connected": False,
        "event_subscriptions_connected": False,
        "agent_execution_authorised": False,
        "needs": (
            "explicit_trigger_and_cadence",
            "verified_first_party_runtime",
            "guardian_permission_review",
            "hrm_receipts_and_idempotency",
            "failure_recovery_and_stop_control",
            "Founder Final",
        ),
        "founder_final": True,
    }


def mission_step_skill_review(mission: str) -> dict[str, Any]:
    """Skill-first, fail-closed advisory routing per canonical protocol step.

    Passport descriptions are declared skills, not execution proof. No selected
    agent is activated, given a permission, or moved from its family home.
    """
    if not isinstance(mission, str) or not mission.strip():
        raise ValueError("Mission brief required")
    brief = " ".join(mission.split())[:800]
    directory = room_directory()  # Enforce all existing registry and family checks.
    members = {str(item["agent_id"]): item for item in agents.AGENT_REGISTRY}
    homes = {room["agent_ids"][0]: room for room in directory["rooms"]
             if room["kind"] == "individual"}
    mission_terms = {term for term in re.findall(r"[a-z]{4,}", brief.casefold())
                     if term not in {"that", "this", "with", "from", "please", "mission", "review", "system"}}
    steps: list[dict[str, Any]] = []
    for protocol in ai_behaviour_protocol.AI_BEHAVIOUR_PARTS:
        step_id = str(protocol["id"])
        requirements = _STEP_SKILL_TERMS.get(step_id)
        if requirements is None:
            raise ValueError("Unmapped canonical protocol step")
        matches: list[tuple[int, int, str, tuple[str, ...], tuple[str, ...]]] = []
        for agent_id, agent in members.items():
            if agent.get("registry_status") != "ACTIVE":
                continue
            mind = agent.get("mind") or {}
            capabilities = tuple(str(skill).casefold() for skill in mind.get("capabilities", ()))
            declared_role = str(agent.get("role") or "").casefold()
            found = tuple(term for term in requirements
                          if any(term in skill for skill in capabilities)
                          or term in declared_role)
            if found:
                declared = " ".join((*capabilities, declared_role))
                mission_hits = tuple(sorted(term for term in mission_terms if term in declared))
                # Step skills take precedence; mission relevance breaks ties only.
                matches.append((len(found), len(mission_hits), agent_id, found, mission_hits))
        matches.sort(key=lambda item: (-item[0], -item[1], item[2]))
        best = matches[0] if matches else None
        selection = None
        if best is not None:
            agent_id = best[2]
            agent = members[agent_id]
            home = homes[agent_id]
            selection = {
                "agent_id": agent_id,
                "name": str(agent["name"]),
                "family_id": home["family_id"],
                "home_system": home["home_system"],
                "matched_declared_skills": best[3],
                "matched_mission_terms": best[4],
                "selection_basis": "passport_step_skills_then_mission_relevance",
                "runtime_skill_verified": False,
                "availability": "unknown",
                "execution_authorised": False,
            }
        steps.append({
            "step_id": step_id,
            "label": str(protocol["label"]),
            "required_skill_terms": requirements,
            "recommendation": selection,
            "qualified_runtime_agent": None,
            "match_status": (
                "declared_skill_match_unverified" if best else "no_declared_skill_match"
            ),
            "matched_candidate_count": len(matches),
            "authority_gates_remain": _AUTHORITY_GATES,
        })
    handoffs: list[dict[str, Any]] = []
    for previous, following in pairwise(steps):
        sender = previous["recommendation"]
        receiver = following["recommendation"]
        # A candidate is never a verified speaker. Do not create a message or
        # attribute a statement to an agent without an authenticated runtime.
        handoffs.append({
            "from_step": previous["step_id"],
            "to_step": following["step_id"],
            "from_agent_id": sender["agent_id"] if sender else None,
            "to_agent_id": receiver["agent_id"] if receiver else None,
            "from_family_id": sender["family_id"] if sender else None,
            "to_family_id": receiver["family_id"] if receiver else None,
            "cross_family": (
                sender["family_id"] != receiver["family_id"]
                if sender and receiver else None
            ),
            "state": (
                "advisory_unverified" if sender and receiver
                else "blocked_missing_skill_match"
            ),
            "required_proof": (
                "authenticated_sender",
                "registered_receiver",
                "permission_check",
                "attributable_evidence",
                "HRM_receipt",
                "Guardian_review",
            ),
            "message_sent": False,
            "delivery_verified": False,
            "authority_transferred": False,
        })
    return {
        "mission": brief,
        "mode": "skill_first_step_review_only",
        "protocol_source": ai_behaviour_protocol.PROTOCOL_NAME,
        "steps": tuple(steps),
        "proposed_handoffs": tuple(handoffs),
        "council_review": _council_review_template(),
        "automation_review": _automation_review_template(brief),
        "handoff_messages_sent": 0,
        "founder_final": True,
        "can_execute": False,
        "agent_messages_sent": False,
        "runtime_skills_proven": False,
    }
