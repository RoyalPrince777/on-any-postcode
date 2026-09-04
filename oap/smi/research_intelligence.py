"""Governed Research Intelligence cluster for Sovereign Megaverse Intelligence.

Research Intelligence is a specialist SMI capability cluster, not an eighth
Intelligence World and not an autonomous authority. It coordinates existing OAP
retrieval, evidence, memory and synthesis capabilities under Guardian, HRM and
Human Authority.
"""

from __future__ import annotations

RESEARCH_INTELLIGENCE_REVISION = "2026-09-04-v1"

RESEARCH_STAGES = (
    "scope_question",
    "retrieve_evidence",
    "classify_sources",
    "verify_claims",
    "compare_and_challenge",
    "synthesise_findings",
    "record_provenance_and_freshness",
)

CAPABILITY_IDS = (
    "cited_live_research",
    "parallel_retrieval",
    "evidence_first",
    "long_context_synthesis",
    "live_signal_awareness",
    "multi_expert_synthesis",
    "gap_adversarial_review",
    "context_tiering",
    "context_compaction",
    "memory_reconstruction",
)

SOURCE_CLASSES = (
    "first_party_or_official",
    "standards_or_academic",
    "reputable_secondary",
    "authorised_internal_oap",
    "community_or_social_signal",
)

PROVENANCE_FIELDS = (
    "source",
    "source_class",
    "published_at",
    "retrieved_at",
    "freshness",
    "claim_supported",
    "confidence",
    "observed_or_inferred",
)


def depth_for_complexity(level: str | None) -> int:
    """Map Research Intelligence depth onto SMI's existing 3/7/21 model."""

    value = str(level or "standard").strip().casefold()
    if value in {"quick", "instant", "3"}:
        return 3
    if value in {"deep", "high", "21"}:
        return 21
    return 7


def status() -> dict[str, object]:
    return {
        "component": "SMI Research Intelligence",
        "ready": True,
        "revision": RESEARCH_INTELLIGENCE_REVISION,
        "specialist_cluster": True,
        "intelligence_world": False,
        "creates_eighth_world": False,
        "stage_count": len(RESEARCH_STAGES),
        "capability_count": len(CAPABILITY_IDS),
        "source_class_count": len(SOURCE_CLASSES),
        "provenance_fields": PROVENANCE_FIELDS,
        "adaptive_depths": (3, 7, 21),
        "primary_sources_preferred": True,
        "freshness_tracking": True,
        "claim_source_linking": True,
        "contradiction_detection": True,
        "deduplication": True,
        "observable_vs_inferred_labels": True,
        "citation_fabrication_allowed": False,
        "unsupported_completion_claims_allowed": False,
        "private_chain_of_thought_exposed": False,
        "autonomous_canonical_promotion": False,
        "consequential_execution_authority": False,
        "guardian_required": True,
        "hrm_audit_required": True,
        "human_authority_final": True,
    }
