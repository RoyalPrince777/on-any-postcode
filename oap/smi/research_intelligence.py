"""Governed Research Intelligence cluster for Sovereign Megaverse Intelligence.

Research Intelligence is a specialist SMI capability cluster, not an eighth
Intelligence World and not an autonomous authority. It coordinates existing OAP
retrieval, evidence, memory and synthesis capabilities under Guardian, HRM and
Human Authority.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from decimal import Decimal, InvalidOperation

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

# CC21 reuses the Research Intelligence cluster. This only classifies
# caller-supplied observations; it never fetches prices, publishes signals,
# writes SIKA ledger entries, recommends trades, or executes transactions.
FINANCIAL_OBSERVATION_MAX_AGE_SECONDS = 900
_FINANCIAL_DISALLOWED_FIELDS = frozenset({
    "trade_action", "auto_execute", "payment_instruction", "ledger_entry",
    "win_rate", "profit_loss", "guaranteed_return",
})


def assess_financial_observation(
    observation: Mapping[str, object],
    *,
    now: datetime,
    trusted_sources: Mapping[str, Mapping[str, object]] | None = None,
) -> dict[str, object]:
    """Fail closed on provenance, freshness, permission and quote integrity.

    Caller must supply a timezone-aware now and an independently provisioned
    source registry. Untrusted observation permission flags grant no authority.
    Passing observations remain research-only, never trade signals.
    """
    if now.tzinfo is None or now.utcoffset() is None:
        raise ValueError("now must be timezone-aware")

    reasons: list[str] = []
    source_class = observation.get("source_class")
    if not str(observation.get("source") or "").strip():
        reasons.append("missing_source")
    if source_class not in SOURCE_CLASSES:
        reasons.append("invalid_source_class")
    if source_class == "community_or_social_signal":
        reasons.append("social_signal_not_a_verified_quote")
    # Observations are untrusted input. Permission and source assurance cannot
    # be granted by flags that the observation supplies about itself.
    source_id = str(observation.get("source") or "").strip()
    source_record = (trusted_sources or {}).get(source_id)
    if not isinstance(source_record, Mapping):
        reasons.append("untrusted_source")
    else:
        if source_record.get("research_use_permitted") is not True:
            reasons.append("research_permission_not_proven")
        if source_record.get("verified") is not True:
            reasons.append("source_not_verified")
        if source_record.get("source_class") != source_class:
            reasons.append("source_class_mismatch")
        instruments = source_record.get("instruments")
        if (
            not isinstance(instruments, (tuple, list, frozenset))
            or observation.get("instrument") not in instruments
        ):
            reasons.append("instrument_not_authorised")
    if observation.get("claim_supported") is not True:
        reasons.append("claim_not_verified")
    if observation.get("observed_or_inferred") != "observed":
        reasons.append("not_a_direct_observation")
    if not str(observation.get("instrument") or "").strip():
        reasons.append("missing_instrument")
    if _FINANCIAL_DISALLOWED_FIELDS.intersection(observation):
        reasons.append("execution_or_performance_claim_in_quote")

    try:
        quote = Decimal(str(observation["value"]))
        if not quote.is_finite() or quote <= 0:
            reasons.append("invalid_quote")
    except (KeyError, ValueError, TypeError, InvalidOperation):
        reasons.append("invalid_quote")

    timestamps: dict[str, datetime] = {}
    for field in ("published_at", "observed_at", "retrieved_at"):
        raw = observation.get(field)
        try:
            if not isinstance(raw, str):
                raise TypeError("timestamp must be a string")
            parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
            if parsed.tzinfo is None or parsed.utcoffset() is None:
                raise ValueError("timestamp requires timezone")
            timestamps[field] = parsed
        except (TypeError, ValueError, OverflowError):
            reasons.append("invalid_" + field)

    if len(timestamps) == 3:
        published, observed, retrieved = (
            timestamps[field] for field in ("published_at", "observed_at", "retrieved_at")
        )
        if not (published <= observed <= retrieved <= now):
            reasons.append("inconsistent_or_future_timestamps")
        elif (now - observed).total_seconds() > FINANCIAL_OBSERVATION_MAX_AGE_SECONDS:
            reasons.append("stale_observation")

    return {
        "usable_for_research": not reasons,
        "reasons": tuple(reasons),
        "read_only": True,
        "trade_signal": False,
        "execution_allowed": False,
        "ledger_write_allowed": False,
        "human_authority_final": True,
        "source": str(observation.get("source") or "").strip(),
    }
