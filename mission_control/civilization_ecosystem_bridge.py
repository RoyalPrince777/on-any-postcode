"""Read-only evidence crosswalk: canonical Civilization owners ↔ Ecosystem domains.

Mappings describe analytical relevance, never an observed causal relationship.
Only the existing Ecosystem runtime supplies signals; missing coverage stays missing.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from typing import Any

from . import civilization, ecosystem_intelligence, ecosystem_runtime

# Explicit registry-owned relevance mapping. Do not turn gaps (e.g.
# communication telemetry) into fabricated observations.
DOMAIN_CROSSWALK: dict[str, tuple[str, ...]] = {
    "people": ("people",),
    "place": ("place",),
    "movement": ("movement",),
    "communication": ("people", "trust"),
    "economy": ("economy",),
    "culture": ("culture",),
    "institutions": ("trust", "place"),
    "environment": ("nature", "infrastructure"),
    "safety": ("trust", "risk"),
}


def project(signals: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Project an existing signal pack without network access or execution.

    A domain has coverage only from actual input signals; a relevant mapped
    source is not proof of the specialist domain's own runtime or external data.
    Individual signal summaries, identity or location are not copied into this
    compact Founder status projection.
    """
    registry = tuple(civilization.CIVILIZATION_DOMAINS)
    allowed = set(ecosystem_intelligence.ECOSYSTEM_DOMAINS)
    registered = {entry["id"] for entry in registry}
    if registered != set(DOMAIN_CROSSWALK):
        raise ValueError("Civilization/Ecosystem domain mapping is out of sync")
    if any(set(values) - allowed for values in DOMAIN_CROSSWALK.values()):
        raise ValueError("Unknown Ecosystem source domain in crosswalk")

    items = tuple(signals)
    counts: Counter[str] = Counter()
    truths: dict[str, Counter[str]] = {item["id"]: Counter() for item in registry}
    for signal in items:
        source = str(signal.get("domain") or "").strip().lower()
        if source not in allowed:
            raise ValueError("Unknown Ecosystem signal domain")
        state = str(signal.get("truth_state") or "").strip().lower()
        if state not in ecosystem_intelligence.TRUTH_STATES:
            raise ValueError("Unrecognised signal truth state")
        if not signal.get("source") or not signal.get("evidence"):
            # An unreferenced observation is never allowed to create coverage.
            continue
        for key, mapped in DOMAIN_CROSSWALK.items():
            if source in mapped:
                counts[key] += 1
                truths[key][state] += 1

    domains = tuple(
        {
            "id": entry["id"],
            "name": entry["name"],
            "owner": entry["owner"],
            "mapped_ecosystem_domains": DOMAIN_CROSSWALK[entry["id"]],
            "referenced_signal_count": counts[entry["id"]],
            "truth_state_counts": dict(truths[entry["id"]]),
            "state": "referenced_internal_context" if counts[entry["id"]] else "no_evidence",
            "operational_proven": False,
        }
        for entry in registry
    )
    return {
        "classification": "read_only_civilization_ecosystem_crosswalk",
        "scope": "founder_internal",
        "domain_count": len(domains),
        "domains_with_referenced_context": sum(bool(item["referenced_signal_count"]) for item in domains),
        "domains": domains,
        "mapping_is_causality_proof": False,
        "internal_context_is_live_external_proof": False,
        "all_civilization_domains_operational_green": False,
        "execution_granted": False,
        "public_personal_data_exposed": False,
        "human_authority_final": True,
    }


def current_state() -> dict[str, Any]:
    """Use the owned internal signal collector, not a second data source."""
    return project(ecosystem_runtime.collect_internal_signals())
