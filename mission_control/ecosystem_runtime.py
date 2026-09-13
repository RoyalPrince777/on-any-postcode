"""Automatic, evidence-bound runtime for OAP Ecosystem Intelligence.

This module turns owned OAP runtime proof into a real internal signal pack,
computes pressure dimensions, applies extended Matrix review lenses without
pretending unregistered candidates are agents, and records Founder-approved
outcomes through HRM receipts. It never performs operational execution.
"""
from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from typing import Any

from . import ecosystem_intelligence, intelligence_runtime_proof, smi_receipt_backend

WORLD_DOMAIN_MAP: dict[str, str] = {
    "earth": "nature",
    "language": "culture",
    "life": "people",
    "movement": "movement",
    "civic": "place",
    "civilisation": "culture",
    "matrix": "infrastructure",
}

DOMAIN_DIMENSIONS: dict[str, tuple[str, ...]] = {
    "people": ("demand", "trust"),
    "place": ("demand", "opportunity_strength"),
    "movement": ("movement", "demand"),
    "economy": ("economic", "demand", "opportunity_strength"),
    "culture": ("cultural_energy", "opportunity_strength"),
    "nature": ("environmental",),
    "infrastructure": ("infrastructure", "recovery_capacity"),
    "trust": ("trust",),
    "opportunity": ("opportunity_strength",),
    "risk": ("infrastructure", "trust"),
}

EXTERNAL_SOURCE_GATES: tuple[dict[str, str], ...] = (
    {"id": "weather_environment", "domain": "nature", "required": "live weather/environment source proof"},
    {"id": "movement_navigation", "domain": "movement", "required": "production navigation/transport source proof"},
    {"id": "civic_public_services", "domain": "place", "required": "current public-service/civic source proof"},
    {"id": "culture_provenance", "domain": "culture", "required": "provenance-backed culture/history source proof"},
    {"id": "infrastructure_telemetry", "domain": "infrastructure", "required": "live infrastructure/network telemetry proof"},
    {"id": "market_activity", "domain": "economy", "required": "real Market demand/supply/fulfilment evidence"},
    {"id": "people_aggregate", "domain": "people", "required": "privacy-safe aggregate participation evidence"},
    {"id": "trust_guardian", "domain": "trust", "required": "live Guardian/trust boundary evidence"},
)


def _runtime_pressure(proof: Mapping[str, Any]) -> int:
    if proof.get("full_runtime_ready"):
        return 10
    if proof.get("live_external_ready"):
        return 20
    if proof.get("bounded_runtime_ready"):
        return 35
    return 70


def collect_internal_signals() -> tuple[dict[str, Any], ...]:
    """Build a real signal pack from the owned runtime-proof matrix."""

    proof = intelligence_runtime_proof.status()
    signals: list[dict[str, Any]] = []
    for item in proof["worlds"]:
        world_id = str(item["id"])
        domain = WORLD_DOMAIN_MAP[world_id]
        pressure = _runtime_pressure(item)
        signals.append(
            {
                "domain": domain,
                "horizon": "now",
                "truth_state": "observed",
                "summary": f"{item['name']} runtime proof: bounded={bool(item['bounded_runtime_ready'])}, live_external={bool(item['live_external_ready'])}, full={bool(item['full_runtime_ready'])}",
                "source": "oap_intelligence_runtime_proof",
                "evidence": (str(item["bounded_evidence"]),),
                "pressure": pressure,
                "confidence": 100,
                "geography": {"global": "OAP World"},
                "affected_systems": (str(item["name"]),),
                "risk": str(item["next_gate"]) if pressure >= 35 else "",
                "recommendation": str(item["next_gate"]),
            }
        )
    return tuple(signals)


def auto_pressure_scores(signals: Iterable[Mapping[str, Any]]) -> dict[str, int]:
    """Compute all nine pressure dimensions from evidence-bound input signals."""

    values: dict[str, list[int]] = {
        key: [] for key in ecosystem_intelligence.PRESSURE_DIMENSIONS
    }
    all_pressures: list[int] = []
    for signal in signals:
        domain = str(signal.get("domain") or "").strip().lower()
        pressure = int(signal.get("pressure") or 0)
        pressure = max(0, min(pressure, 100))
        all_pressures.append(pressure)
        for dimension in DOMAIN_DIMENSIONS.get(domain, ()):
            if dimension == "recovery_capacity":
                continue
            values[dimension].append(pressure)

    default_pressure = round(sum(all_pressures) / len(all_pressures)) if all_pressures else 0
    result: dict[str, int] = {}
    for dimension in ecosystem_intelligence.PRESSURE_DIMENSIONS:
        if dimension == "recovery_capacity":
            infrastructure = values["infrastructure"] or all_pressures
            fragility = max(infrastructure) if infrastructure else 0
            result[dimension] = max(0, 100 - fragility)
        elif values[dimension]:
            result[dimension] = round(sum(values[dimension]) / len(values[dimension]))
        else:
            result[dimension] = default_pressure
    return result


def extended_matrix_lenses(signals: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Apply Tank/Dozer/Smith/Twinz as system lenses, not registered emitters."""

    items = tuple(signals)
    pressures = [int(item.get("pressure") or 0) for item in items]
    sources = [str(item.get("source") or "") for item in items]
    domains = [str(item.get("domain") or "") for item in items]
    truth_states = [str(item.get("truth_state") or "") for item in items]
    source_counts = Counter(source for source in sources if source)
    domain_pressure: dict[str, list[int]] = {}
    for item in items:
        domain_pressure.setdefault(str(item.get("domain") or "unknown"), []).append(
            int(item.get("pressure") or 0)
        )
    domain_average = {
        domain: round(sum(vals) / len(vals)) for domain, vals in domain_pressure.items()
    }
    ordered = sorted(domain_average.items(), key=lambda pair: pair[1])
    return {
        "classification": "extended_matrix_system_lenses_not_registered_agents",
        "Tank": {
            "role": "operational state",
            "max_pressure": max(pressures, default=0),
            "signal_count": len(items),
        },
        "Dozer": {
            "role": "infrastructure resilience",
            "recovery_capacity": auto_pressure_scores(items)["recovery_capacity"],
        },
        "Agent Smith": {
            "role": "integrity and duplication challenge",
            "duplicate_sources": tuple(
                source for source, count in source_counts.items() if count > 1
            ),
            "mixed_truth_states": len(set(truth_states)) > 1,
        },
        "Twinz": {
            "role": "dual-path contradiction comparison",
            "lowest_pressure_domain": ordered[0] if ordered else None,
            "highest_pressure_domain": ordered[-1] if ordered else None,
            "domain_count": len(set(domains)),
        },
        "can_emit_matrix_signal": False,
        "agent_registry_changed": False,
    }


def ingestion_status() -> dict[str, Any]:
    proof = intelligence_runtime_proof.status()
    live_worlds = tuple(
        item["id"] for item in proof["worlds"] if item["live_external_ready"]
    )
    internal_signals = collect_internal_signals()
    return {
        "automatic_internal_ingestion": True,
        "internal_adapter": "all_intelligence_runtime_proof",
        "internal_signal_count": len(internal_signals),
        "live_external_worlds": live_worlds,
        "live_external_signal_count": len(live_worlds),
        "external_source_gates": EXTERNAL_SOURCE_GATES,
        "all_required_live_sources_proven": False,
        "network_calls_made": False,
        "execution_granted": False,
    }


def current_state() -> dict[str, Any]:
    """Return the automatic internal Ecosystem state without external actions."""

    signals = collect_internal_signals()
    scores = auto_pressure_scores(signals)
    analysis = ecosystem_intelligence.analyse(
        signals,
        scope="OAP Internal Runtime",
        pressure_scores=scores,
    )
    return {
        "mode": "automatic_internal_runtime",
        "analysis": analysis,
        "pressure_scores": scores,
        "extended_matrix_lenses": extended_matrix_lenses(signals),
        "ingestion": ingestion_status(),
        "external_live_complete": False,
        "execution_granted": False,
        "human_authority_final": True,
    }


def record_outcome(
    *,
    analysis_id: str,
    decision: str,
    outcome: str,
    evidence: Iterable[object] = (),
    founder_approved: bool,
) -> dict[str, Any]:
    """Record an approved Ecosystem outcome as an HRM learning receipt."""

    if not founder_approved:
        return {
            "ok": False,
            "status": "blocked_founder_approval_required",
            "learning_candidate": False,
            "execution_granted": False,
        }
    if not str(analysis_id).strip() or not str(decision).strip() or not str(outcome).strip():
        return {
            "ok": False,
            "status": "analysis_decision_outcome_required",
            "learning_candidate": False,
            "execution_granted": False,
        }

    receipt = smi_receipt_backend.write_receipt(
        "ecosystem_outcome_receipt",
        {
            "brain_part": "ecosystem_intelligence",
            "gate": 7,
            "command": "record_ecosystem_outcome",
            "signal": "🟢",
            "founder_final": "approved",
            "safe_payload": {
                "analysis_id": str(analysis_id).strip(),
                "decision": str(decision).strip(),
                "outcome": str(outcome).strip(),
                "evidence": tuple(str(item).strip() for item in evidence if str(item).strip()),
                "external_action": False,
            },
        },
    )
    return {
        "ok": bool(receipt.get("ok")),
        "status": "learning_receipt_recorded" if receipt.get("ok") else "learning_receipt_failed",
        "receipt": receipt,
        "learning_candidate": bool(receipt.get("ok")),
        "durable_learning_proven": bool(receipt.get("durable")),
        "recursive_self_improvement_handoff": bool(receipt.get("ok")),
        "execution_granted": False,
        "human_authority_final": True,
    }


def status() -> dict[str, Any]:
    config = smi_receipt_backend.backend_configuration_status()
    ingestion = ingestion_status()
    return {
        "name": "OAP Ecosystem Runtime",
        "automatic_internal_ingestion_ready": ingestion["automatic_internal_ingestion"],
        "computed_pressure_scoring_ready": True,
        "cross_postcode_learning_ready": True,
        "founder_decision_pack_ready": True,
        "outcome_receipt_ready": True,
        "durable_hrm_backend_configured": config["durable_backend_configured"],
        "durable_hrm_backend": config["preferred_backend"],
        "external_live_complete": False,
        "external_source_gates": EXTERNAL_SOURCE_GATES,
        "extended_matrix_lenses_ready": True,
        "extended_matrix_agents_promoted": False,
        "agent_registry_changed": False,
        "execution_granted": False,
        "human_authority_final": True,
    }
