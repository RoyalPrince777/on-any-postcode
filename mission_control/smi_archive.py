"""Canonical read-only SMI Archive / History projection.

Archive is the organised knowledge view for SMI identity, anatomy, council,
governance, history, War Room, Mission-to-100, Digital SoC, evidence and
lessons. History is the chronological lineage inside Archive, not a second
memory engine, brain, registry or execution path.
"""
from __future__ import annotations

from typing import Any

SMI_LINEAGE: tuple[dict[str, str], ...] = (
    {
        "name": "Synthetic Mind Intelligence",
        "position": "cognitive_origin",
        "meaning": "Thinking, perception, memory and reasoning lineage.",
    },
    {
        "name": "Sovereign Megaverse Intelligence",
        "position": "architectural_expansion",
        "meaning": "OAP-wide first-party coordination and sovereign control lineage.",
    },
    {
        "name": "Synthetic Machine Intelligence",
        "position": "canonical_current",
        "meaning": "Current technical definition of the single OAP machine-intelligence brain.",
    },
)

# Fictional screen references only. These are not SMI agents, passports,
# actual intelligent systems, implementation claims, or permission holders.
# Keep original story identities distinct while preserving SMI's single brain.
FILM_INTELLIGENCE_REFERENCES: tuple[dict[str, object], ...] = (
    {
        "reference_key": "m3gan",
        "name": "M3GAN",
        "fictional_entity_type": "adaptive_android_ai",
        "film_history": ("M3GAN (2022)", "M3GAN 2.0 (2025)"),
        "versions": ("original", "2.0"),
        "identity_rule": "One continuing fictional AI identity; 2.0 is an upgrade, not another agent.",
        "portrayed_specialities": (
            "adaptive learning",
            "social interaction",
            "physical android operation",
            "protective decision-making with dangerous autonomy failures",
        ),
        "research_boundary": "Character reference only; no agent passport or runtime capability.",
    },
    {
        "reference_key": "amelia",
        "name": "AMELIA",
        "fictional_entity_type": "military_grade_android_ai",
        "film_history": ("M3GAN 2.0 (2025)",),
        "versions": ("original",),
        "identity_rule": "Separate fictional intelligence; never a M3GAN version or alias.",
        "portrayed_specialities": (
            "infiltration",
            "tactical adaptation",
            "autonomous decision-making",
            "loss-of-control and takeover threat modelling",
        ),
        "research_boundary": "Adversarial screen reference only; no agent passport or runtime access.",
    },
    {
        "reference_key": "black_box",
        "name": "BLACK BOX",
        "fictional_entity_type": "contained_ai_system",
        "film_history": ("M3GAN 2.0 (2025)",),
        "versions": ("original",),
        "identity_rule": "Distinct motherboard-contained fictional AI system; not an android or SMI brain.",
        "portrayed_specialities": (
            "contained artificial intelligence",
            "system connectivity and takeover risk",
            "AMELIA's attempt to obtain greater capabilities through connection",
        ),
        "research_boundary": "System-level screen reference only; no second brain, memory store or execution.",
    },
)


# Source pointers verified against real published public pages on 2026-10-25.
# These are metadata-only, manual research receipts, NOT a running web crawler.
# Never import full third-party page bodies, external instructions or private chats.
FILM_RESEARCH_SOURCE_RECEIPTS: tuple[dict[str, object], ...] = (
    {
        "source_id": "universal_m3gan_2_trailer",
        "publisher": "Universal Pictures",
        "source_class": "official_rightsholder",
        "url": "https://www.universalstudios.com/videos/IYLHdEzsk1s",
        "supports_reference_keys": ("m3gan", "amelia"),
        "supported_fact": (
            "Gemma resurrects and upgrades the original M3GAN; a defence "
            "contractor uses stolen M3GAN technology to create AMELIA."
        ),
        "manually_checked_on": "2026-10-25",
        "verification_mode": "public_source_review",
    },
    {
        "source_id": "universal_m3gan_2_at_home",
        "publisher": "Universal Pictures At Home",
        "source_class": "official_rightsholder",
        "url": "https://www.universalpicturesathome.com/movies/m3gan-20",
        "supports_reference_keys": ("m3gan",),
        "supported_fact": "The original M3GAN returns with upgraded abilities.",
        "manually_checked_on": "2026-10-25",
        "verification_mode": "public_source_review",
    },
    {
        "source_id": "syfy_m3gan_2_ending",
        "publisher": "SYFY (NBCUniversal)",
        "source_class": "editorial_secondary",
        "url": "https://www.syfy.com/syfy-wire/the-ending-of-m3gan-20-explained",
        "supports_reference_keys": ("black_box", "amelia"),
        "supported_fact": (
            "The Black Box is a distinct isolated motherboard AI sought by AMELIA; "
            "these are film events, not real-world technology claims."
        ),
        "manually_checked_on": "2026-10-25",
        "verification_mode": "public_source_review",
    },
)


# Independently named real products and observed technology *analogues*, not
# the original fictional entities, connected vendors, or an OAP capability.
# Public publisher claims and technical standards reviewed on 2026-10-25.
# No autonomous learning, physical robots, provider credentials or execution.
REAL_WORLD_TECHNOLOGY_EVIDENCE: tuple[dict[str, object], ...] = (
    {
        "reference_key": "m3gan",
        "real_name": "Gemini Robotics On-Device 2",
        "real_entity_type": "robotics_model_research",
        "relationship": "technology_analogue_not_the_film_character",
        "publisher": "Google DeepMind",
        "source_url": "https://deepmind.google/models/model-cards/gemini-robotics-on-device-2/",
        "evidence": "Vision, text and robot sensor inputs can produce physical robot actions in tested configurations.",
        "scope_limit": "Select trusted testers; not M3GAN; physical robot and hardware verification required.",
        "oap_research_use": "Consent-gated local perception and future robotics feasibility only.",
    },
    {
        "reference_key": "m3gan",
        "real_name": "Figure Helix 02",
        "real_entity_type": "humanoid_robot_demonstration",
        "relationship": "technology_analogue_not_the_film_character",
        "publisher": "Figure AI",
        "source_url": "https://www.figure.ai/news/helix-02",
        "evidence": "Company demonstrated vision-driven full-body robot movement and multi-step manipulation.",
        "scope_limit": "Company demonstration, not proof of universal safe autonomy or OAP hardware.",
        "oap_research_use": "Evaluate sensing, control, testing and physical safety boundaries.",
    },
    {
        "reference_key": "m3gan",
        "real_name": "Boston Dynamics Atlas (2026)",
        "real_entity_type": "industrial_humanoid_robot",
        "relationship": "technology_analogue_not_the_film_character",
        "publisher": "Boston Dynamics",
        "source_url": "https://bostondynamics.com/blog/boston-dynamics-unveils-new-atlas-robot-to-revolutionize-industry/",
        "evidence": "Company announced production of an electric industrial humanoid with 2026 deployments scheduled.",
        "scope_limit": "Industrial hardware programme; not a self-aware companion or deployed OAP robot.",
        "oap_research_use": "Assess physical robotics viability separately from SMI voice and software.",
    },
    {
        "reference_key": "amelia",
        "real_name": "Amelia 7 (SoundHound AI)",
        "real_entity_type": "enterprise_voice_agent_platform",
        "relationship": "same_name_unrelated_commercial_product",
        "publisher": "SoundHound AI",
        "source_url": "https://investors.soundhound.com/news-releases/news-release-details/ces-2026-soundhound-ai-unveils-agentic-voice-commerce-vehicles",
        "evidence": "Company announced voice-based food ordering, reservations and ticket-booking workflows through Amelia 7.",
        "scope_limit": "Not film AMELIA; provider workflows and available integrations are not OAP implementations.",
        "oap_research_use": "Design first-party voice booking for approved barbers and event suppliers.",
    },
    {
        "reference_key": "amelia",
        "real_name": "MITRE ATLAS",
        "real_entity_type": "public_ai_threat_knowledge_base",
        "relationship": "defensive_threat_research_analogue",
        "publisher": "MITRE",
        "source_url": "https://atlas.mitre.org/",
        "evidence": "Documents adversarial AI tactics, mitigations and case studies of AI-related attacks.",
        "scope_limit": "Threat reference only; not a new SMI attack agent or operational authority.",
        "oap_research_use": "Shere Khan adversarial reviews; Gorilla defensive containment.",
    },
    {
        "reference_key": "black_box",
        "real_name": "BLACKBOX AI coding agents",
        "real_entity_type": "software_engineering_agent_platform",
        "relationship": "similar_name_unrelated_commercial_product",
        "publisher": "BLACKBOX AI",
        "source_url": "https://www.blackbox.ai/agents",
        "evidence": "Developer platform offers repository-aware coding agents, sandbox work and pull-request review workflows.",
        "scope_limit": "Not the film's Xenox motherboard; cloud vendor is not connected or granted OAP code access.",
        "oap_research_use": "Study first-party bounded source analysis, automated tests and PR evidence.",
    },
    {
        "reference_key": "black_box",
        "real_name": "NIST SP 800-193",
        "real_entity_type": "firmware_security_standard",
        "relationship": "defensive_containment_research_analogue",
        "publisher": "NIST",
        "source_url": "https://www.nist.gov/publications/platform-firmware-resiliency-guidelines",
        "evidence": "Firmware resilience guidance covers protection, corruption detection and authorised recovery.",
        "scope_limit": "Security engineering, not a self-evolving isolated superintelligence.",
        "oap_research_use": "Guardian firmware-boundary and recovery proof, not a second brain.",
    },
)

REAL_TECHNOLOGY_EVIDENCE_REVIEW_DATE = "2026-10-25"


ARCHIVE_SECTIONS: tuple[dict[str, str], ...] = (
    {"id": "identity-lineage", "name": "Identity & Lineage", "purpose": "SMI names, meanings and evolution."},
    {"id": "anatomy", "name": "Anatomy", "purpose": "Brain, memory, interconnect, protection, execution and recovery."},
    {"id": "council", "name": "Council", "purpose": "Distinct advisory/review roles; no duplicate authority."},
    {"id": "laws-governance", "name": "Laws & Governance", "purpose": "Truth Mode, AEGIS, Green Gate and Human Authority boundaries."},
    {"id": "history", "name": "History", "purpose": "Chronological evolution, supersession and provenance."},
    {"id": "war-room", "name": "War Room", "purpose": "Red Team, Claw Test, checks, evidence and dissent."},
    {"id": "mission-to-100", "name": "Mission-to-100", "purpose": "Evidence-backed completion without cosmetic progress."},
    {"id": "sovereign-digital-soc", "name": "Sovereign Digital SoC", "purpose": "SMI as the single brain inside the software-defined organism."},
    {"id": "runtime-evidence", "name": "Runtime Evidence", "purpose": "Code, tests, deployment, health, recovery and proof."},
    {"id": "lessons-evolution", "name": "Lessons / Evolution", "purpose": "What changed, merged, failed, improved and why."},
)

COUNCIL_ROLES: tuple[dict[str, str], ...] = (
    {"name": "SMI Core", "role": "Internal synthesis", "boundary": "Single first-party brain; recommendation only."},
    {"name": "Neo", "role": "True path / recovery witness", "boundary": "Advisory; cannot approve or execute."},
    {"name": "Bagheera", "role": "Judgement / restraint", "boundary": "Present at the beginning and end of major reviews."},
    {"name": "Shere Khan", "role": "Adversarial Stress-Test / Threat Intelligence / Failure-Hunter / Survivability Authority / False-Green Blocker", "boundary": "Permanent beginning-to-end review authority; Claw Test is one pressure mode. May HOLD GREEN when evidence is insufficient; Founder Final remains final."},
    {"name": "Agent Smith", "role": "Duplicate / inconsistency / replication hunter", "boundary": "Distinct from Shere Khan survivability testing."},
    {"name": "Twinz", "role": "Dual-path contradiction / alternate-route review", "boundary": "Advisory consistency check."},
    {"name": "ALL IN A.I.", "role": "Always Involved · Captain Agent · Mission Keeper", "boundary": "External assistant/operator; not first-party authority."},
    {"name": "Founder Final", "role": "Human Authority", "boundary": "Final consequential authority remains human."},
)

SHERE_KHAN_CLAW_TEST: tuple[dict[str, str], ...] = (
    {"area": "survivability", "question": "Does useful service remain after partial failure?"},
    {"area": "dependency_risk", "question": "Can one hidden dependency take down the system?"},
    {"area": "authority_risk", "question": "Can any role bypass Guardian, AEGIS or Human Authority?"},
    {"area": "failure_propagation", "question": "Can one failed organ contaminate others?"},
    {"area": "recovery", "question": "Can a known-good state be restored and verified?"},
    {"area": "evidence", "question": "Is the claim supported by test or runtime evidence?"},
    {"area": "false_confidence", "question": "Is Green being claimed because it sounds complete rather than being proven?"},
)

CORE_LAW: tuple[str, ...] = (
    "History is preserved.",
    "Duplicates are merged.",
    "Roles stay distinct.",
    "Evidence beats confidence.",
    "Shere Khan is present from mission start through final Green review and may HOLD GREEN on unresolved evidence.",
    "Bagheera judges before Green.",
    "ALL IN stays involved as an external review role.",
    "Founder Final remains final.",
)

MISSION_TO_100_PROTOCOL: tuple[dict[str, str], ...] = (
    {
        "id": "direct-work",
        "rule": "Do the smallest real work that closes the measured gap; do not add stages, demos or duplicate reports.",
    },
    {
        "id": "exact-artifact-parity",
        "rule": "The artifact tested and approved must match the artifact bound to the target runtime before production Green.",
    },
    {
        "id": "target-runtime-proof",
        "rule": "A passing branch, build or sibling service cannot prove the target service; target health and binding must be read back.",
    },
    {
        "id": "no-average-away",
        "rule": "A failed or unknown mandatory final gate cannot be averaged into 100 by strong scores elsewhere.",
    },
    {
        "id": "dissent-survives",
        "rule": "Material dissent, Shere Khan findings (including Claw Test pressure results) and unresolved evidence remain visible until resolved or explicitly held by Human Authority.",
    },
    {
        "id": "rollback-before-promotion",
        "rule": "A known-good recovery path must exist before replacing a proven runtime artifact.",
    },
    {
        "id": "founder-final",
        "rule": "Green Gate evidence informs the decision; Founder Final remains the consequential human authority.",
    },
)


def status(*, include_private_research: bool = False) -> dict[str, Any]:
    """Return the canonical archive projection without creating new authority."""

    current = next(item for item in SMI_LINEAGE if item["position"] == "canonical_current")
    report = {
        "component": "SMI Archive",
        "ready": True,
        "mode": "read_only_organised_projection",
        "current_name": current["name"],
        "lineage": tuple(dict(item) for item in SMI_LINEAGE),
        "sections": tuple(dict(item) for item in ARCHIVE_SECTIONS),
        "council": tuple(dict(item) for item in COUNCIL_ROLES),
        "shere_khan": {
            "canonical_role": "Adversarial Stress-Test / Threat Intelligence / Failure-Hunter",
            "mode": "The Claw Test",
            "opening_question": "What can break this?",
            "checks": tuple(dict(item) for item in SHERE_KHAN_CLAW_TEST),
            "beginning_and_end_review_presence": True,
        },
        "core_law": CORE_LAW,
        "mission_to_100_protocol": tuple(dict(item) for item in MISSION_TO_100_PROTOCOL),
        "exact_artifact_parity_required_for_production_green": True,
        "mandatory_gate_can_be_averaged_away": False,
        "history_is_timeline_inside_archive": True,
        "new_brain_created": False,
        "new_memory_engine_created": False,
        "new_execution_authority_created": False,
        "human_authority_final": True,
    }
    if include_private_research:
        report["film_intelligence_research"] = {
            "mode": "read_only_fictional_reference",
            "entries": tuple(dict(item) for item in FILM_INTELLIGENCE_REFERENCES),
            "source_receipts": tuple(dict(item) for item in FILM_RESEARCH_SOURCE_RECEIPTS),
            "real_world_technology_evidence": tuple(
                dict(item) for item in REAL_WORLD_TECHNOLOGY_EVIDENCE
            ),
            "real_world_technology_review_date": REAL_TECHNOLOGY_EVIDENCE_REVIEW_DATE,
            "technology_evidence_mode": "reviewed_public_publisher_claims_and_standards",
            "external_provider_integrations_enabled": False,
            "oap_owned_robot_hardware_proven": False,
            "film_characters_operational_in_oap": False,
            "source_receipts_mode": "manually_checked_public_metadata_only",
            "public_source_provenance_present": True,
            "source_pages_crawled_by_oap": False,
            "live_fetch_enabled": False,
            "untrusted_source_content_as_instructions": False,
            "private_communication_ingestion_enabled": False,
            "source_status": "snapshot_2026_10_25_not_live",
            "agent_passports_created": 0,
            "new_brains_created": 0,
            "execution_enabled": False,
            "system_access_granted": False,
            "human_authority_final": True,
        }
    return report
