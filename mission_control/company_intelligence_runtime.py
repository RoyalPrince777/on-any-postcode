"""Live read-only evidence projection for OAP Company Intelligence.

This layer reuses existing OAP Music and Market stores. It never invents evidence:
missing rows, unavailable stores, incomplete rights receipts, or missing margin proof
remain UNKNOWN/CONFLICTING rather than becoming Green.
"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any

from . import (
    company_evidence_ingestion,
    company_intelligence_evidence_registry,
    company_intelligence_evidence_store,
    market_supplier_network,
    music_evidence,
    organism_runtime,
    product_core_services,
)

_COMPANY_NUMBER = "14753133"
_COMPANY_SOURCE = (
    "https://find-and-update.company-information.service.gov.uk/company/14753133"
)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _evidence(
    domain: str,
    state: str,
    source_reference: str,
    *,
    authority_reference: str = "",
    note: str = "",
    observed_at: str | None = None,
) -> dict[str, str]:
    return {
        "domain": domain,
        "state": state,
        "source_reference": source_reference,
        "authority_reference": authority_reference,
        "note": note,
        "observed_at": observed_at or _now(),
    }


def _company_registry_item() -> dict[str, str]:
    """Read one externally verified registry observation from configuration.

    Runtime never scrapes or guesses Companies House state. Human/automation supplied
    source evidence must carry a timestamp and state. Without it, remain UNKNOWN.
    """
    state = os.environ.get("OAP_COMPANY_REGISTRY_EVIDENCE_STATE", "").strip().upper()
    observed = os.environ.get("OAP_COMPANY_REGISTRY_EVIDENCE_AT", "").strip()
    source = os.environ.get("OAP_COMPANY_REGISTRY_EVIDENCE_REF", "").strip()
    note = os.environ.get("OAP_COMPANY_REGISTRY_EVIDENCE_NOTE", "").strip()
    if state in company_evidence_ingestion.ACCEPTED_STATES and observed and source:
        return _evidence(
            "company_registry",
            state,
            source,
            authority_reference="Companies House / competent registry evidence",
            note=note,
            observed_at=observed,
        )
    return _evidence(
        "company_registry",
        "UNKNOWN",
        _COMPANY_SOURCE,
        authority_reference="Companies House",
        note=(
            f"Company {_COMPANY_NUMBER}: no current runtime evidence observation "
            "has been configured."
        ),
    )


def _music_items(identity_id: str) -> tuple[dict[str, str], dict[str, str]]:
    try:
        tune = product_core_services.tune_dashboard(identity_id)
        releases = tuple(tune.get("releases") or ())
    except Exception:  # noqa: BLE001 - store failure must remain unproven.
        return (
            _evidence("artist_rights", "UNAVAILABLE", "oap:music:postgres"),
            _evidence("music_catalogue", "UNAVAILABLE", "oap:music:postgres"),
        )

    if not releases:
        return (
            _evidence(
                "artist_rights",
                "UNKNOWN",
                "oap:music:evidence-chain",
                note="No owner-scoped release exists to evaluate.",
            ),
            _evidence(
                "music_catalogue",
                "UNKNOWN",
                "oap:music:releases",
                note="No owner-scoped catalogue release exists.",
            ),
        )

    store = music_evidence.MusicEvidenceStore()
    rights_ready = True
    checked = 0
    for release in releases:
        release_id = str(release.get("release_id") or "")
        if not release_id:
            rights_ready = False
            continue
        try:
            receipts = store.read_receipts(
                owner_identity_id=identity_id,
                release_id=release_id,
            )
            gate = music_evidence.private_distribution_gate(
                receipts,
                recovery_readback_proven=any(
                    row.get("evidence_kind") == "recovery_readback"
                    for row in receipts
                    if isinstance(row, dict)
                ),
            )
        except Exception:  # noqa: BLE001
            rights_ready = False
            continue
        checked += 1
        if not gate.get("private_handoff_ready"):
            rights_ready = False

    rights_state = "PROVEN" if checked == len(releases) and rights_ready else "CONFLICTING"
    return (
        _evidence(
            "artist_rights",
            rights_state,
            "oap:music:evidence-chain",
            authority_reference="owner-scoped immutable OAP Music evidence receipts",
            note=f"{checked}/{len(releases)} releases evaluated; complete rights gate required.",
        ),
        _evidence(
            "music_catalogue",
            "PROVEN",
            "oap:music:releases",
            authority_reference="owner-scoped OAP Music Postgres",
            note=f"{len(releases)} release(s) present in the owner-scoped catalogue.",
        ),
    )


def _commerce_items(identity_id: str) -> tuple[dict[str, str], ...]:
    try:
        commerce = product_core_services.commerce_dashboard(identity_id)
        bindings = market_supplier_network.STORE.owner_bindings(
            seller_identity_id=identity_id
        )
    except Exception:  # noqa: BLE001
        return (
            _evidence("clothing_supplier", "UNAVAILABLE", "oap:market:supplier-network"),
            _evidence("print_on_demand_supplier", "UNAVAILABLE", "oap:market:supplier-network"),
            _evidence("pricing_margin", "UNAVAILABLE", "oap:market:pricing-margin"),
            _evidence("market_commerce", "UNAVAILABLE", "oap:commerce:postgres"),
        )

    ready_bindings = [
        item
        for item in bindings
        if item.get("state") == "READY" and str(item.get("evidence_reference") or "").strip()
    ]
    supplier_state = "PROVEN" if ready_bindings else "UNKNOWN"
    storefront = commerce.get("storefront")
    market_state = "PROVEN" if storefront is not None else "UNKNOWN"

    margin_ref = os.environ.get("OAP_PRICING_MARGIN_EVIDENCE_REF", "").strip()
    margin_at = os.environ.get("OAP_PRICING_MARGIN_EVIDENCE_AT", "").strip()
    margin_state = "PROVEN" if margin_ref and margin_at else "UNKNOWN"

    return (
        _evidence(
            "clothing_supplier",
            supplier_state,
            "oap:market:supplier-network",
            authority_reference="OAP Supplier Network READY bindings",
            note=f"{len(ready_bindings)} READY supplier binding(s) with evidence.",
        ),
        _evidence(
            "print_on_demand_supplier",
            supplier_state,
            "oap:market:supplier-network",
            authority_reference="OAP made-to-order Supplier Network",
            note=f"{len(ready_bindings)} READY made-to-order supplier binding(s).",
        ),
        _evidence(
            "pricing_margin",
            margin_state,
            margin_ref or "oap:market:pricing-margin",
            authority_reference="Founder-approved cost/price/margin evidence",
            note=(
                "Price alone is not margin proof."
                if margin_state != "PROVEN"
                else "Explicit pricing/margin evidence reference configured."
            ),
            observed_at=margin_at or None,
        ),
        _evidence(
            "market_commerce",
            market_state,
            "oap:commerce:postgres",
            authority_reference="owner-scoped OAP Commerce Core",
            note=(
                f"Storefront connected; {len(commerce.get('products') or [])} product(s), "
                f"{len(commerce.get('orders') or [])} order record(s)."
                if storefront is not None
                else "No owner-scoped storefront is present."
            ),
        ),
    )



# Skilltree-style visibility, not Skilltree software: eight first-party business
# perspectives over the *existing* Company Intelligence evidence snapshot.
# Linked departments indicate useful context, never runnable dependencies.
_DEPARTMENT_LINKS: tuple[tuple[str, str, tuple[str, ...], tuple[str, ...], str], ...] = (
    ("sales", "Sales", ("market_commerce", "pricing_margin"),
     ("deals", "marketing"), "Verify owner-scoped sales and conversion receipts."),
    ("deals", "Deals", (), ("sales", "customer"),
     "Verify first-party deal pipeline, ownership and signed outcomes."),
    ("marketing", "Marketing", ("music_catalogue", "artist_rights"),
     ("sales", "intelligence"), "Verify campaigns, rights and delivery receipts."),
    ("customer", "Customer", (), ("deals", "operations"),
     "Verify owner-scoped customer interaction and support receipts."),
    ("operations", "Operations", ("clothing_supplier", "print_on_demand_supplier"),
     ("customer", "back_office"), "Verify order fulfilment and recovery outcomes."),
    ("back_office", "Back Office", ("company_registry", "pricing_margin"),
     ("operations", "intelligence"), "Verify legal, cost and finance boundaries."),
    ("intelligence", "Intelligence", (), ("knowledge_base", "operations"),
     "Verify attributable agent work and current SMI runtime receipts."),
    ("knowledge_base", "Knowledge Base", (), ("intelligence", "marketing"),
     "Verify owner-scoped knowledge retrieval, sources and freshness."),
)


def department_map(evidence: object, *, protocol_proven_count: int = 0) -> dict[str, Any]:
    """Read-only cross-department lens; never turn source presence into live work.

    No CRM, marketing campaigns, sales figures, autonomous agent outputs or
    inference are invented. Source gaps are carried over from canonical
    Company Intelligence and remain distinct from operational proof.
    """
    states = evidence.get("states") if isinstance(evidence, dict) else None
    states = states if isinstance(states, dict) else {}
    nodes: list[dict[str, Any]] = []
    for department_id, label, keys, connections, action in _DEPARTMENT_LINKS:
        sources = []
        for key in keys:
            row = states.get(key)
            source = row if isinstance(row, dict) else {}
            state = str(source.get("state") or "UNKNOWN").upper()
            # Never trust unnormalised or incomplete evidence as proof.
            if (
                state not in company_evidence_ingestion.ACCEPTED_STATES
                or source.get("valid") is not True
                or not source.get("observed_at")
                or not source.get("source_reference")
            ):
                state = "UNKNOWN"
            sources.append({"domain": key, "state": state})
        blocking = any(
            entry["state"] in {"FAIL", "CONFLICTING", "STALE", "UNAVAILABLE"}
            for entry in sources
        )
        sources_ready = bool(sources) and all(
            entry["state"] == "PROVEN" for entry in sources
        )
        priority_source = next(
            (entry for entry in sources
             if entry["state"] in {"FAIL", "CONFLICTING", "STALE", "UNAVAILABLE"}),
            next((entry for entry in sources if entry["state"] == "UNKNOWN"), None),
        )
        next_proof = (
            f"Verify {priority_source['domain'].replace('_', ' ')} evidence first."
            if priority_source else action
        )
        nodes.append({
            "id": department_id,
            "name": label,
            "linked_departments": connections,
            "source_evidence": tuple(sources),
            "source_state": (
                "BLOCKED" if blocking else
                "SOURCE_PROVEN" if sources_ready else "UNKNOWN"
            ),
            "operational_state": "UNKNOWN",
            "next_safe_action": next_proof,
            "active_agents_claimed": False,
            "revenue_claimed": False,
            "execution_granted": False,
        })
    priority = next(
        (node for node in nodes if node["source_state"] == "BLOCKED"),
        next((node for node in nodes if node["source_state"] == "UNKNOWN"), None),
    )
    return {
        "name": "OAP Company Intelligence · Department Connections",
        "priority_department": priority["name"] if priority else None,
        "priority_next_proof": priority["next_safe_action"] if priority else None,
        "departments": tuple(nodes),
        "department_count": len(nodes),
        "protocol_proven_count": max(0, int(protocol_proven_count)),
        "operational_green": False,
        "founder_final_required": True,
        "read_only": True,
        "no_new_agent_or_brain": True,
        "no_independent_worker_claim": True,
        "no_external_provider_dependency": True,
    }


def swot_first_review(
    evidence: object, departments: object, protocol_registry: object,
) -> dict[str, Any]:
    """Founder-private, read-only SWOT of actual Company Intelligence evidence.

    Strengths are source-observed states, NOT completed live operations.
    Weaknesses and threats retain the original source state. Opportunities
    are proposed proof work, never evidence of commercial execution.
    """
    raw_states = evidence.get("states") if isinstance(evidence, dict) else None
    states = raw_states if isinstance(raw_states, dict) else {}
    strengths: list[dict[str, str]] = []
    weaknesses: list[dict[str, str]] = []
    threats: list[dict[str, str]] = []

    for domain in company_evidence_ingestion.DOMAINS:
        item = states.get(domain)
        item = item if isinstance(item, dict) else {}
        state = str(item.get("state") or "UNKNOWN").upper()
        source = str(item.get("source_reference") or "").strip()
        observed = str(item.get("observed_at") or "").strip()
        if (
            item.get("valid") is not True
            or not source
            or not observed
            or state not in company_evidence_ingestion.ACCEPTED_STATES
        ):
            state = "UNKNOWN"
            source = ""
            observed = ""
        entry = {
            "domain": domain,
            "label": domain.replace("_", " ").title(),
            "state": state,
            "source_reference": source,
            "observed_at": observed,
        }
        if state == "PROVEN":
            strengths.append(entry)
        else:
            weaknesses.append(entry)
            if state in {"CONFLICTING", "STALE", "UNAVAILABLE"}:
                threats.append(entry)

    candidates = (
        departments.get("departments", ())
        if isinstance(departments, dict) else ()
    )
    opportunities = tuple(
        {
            "department": str(node["name"]),
            "next_proof": str(node["next_safe_action"]),
            "state": "PROPOSED",
        }
        for node in candidates
        if isinstance(node, dict)
        and node.get("source_state") in {"BLOCKED", "UNKNOWN"}
        and node.get("name") and node.get("next_safe_action")
    )[:3]
    protocol = protocol_registry if isinstance(protocol_registry, dict) else {}
    return {
        "review": "SMI Company Intelligence · SWOT First",
        "strengths": tuple(strengths),
        "weaknesses": tuple(weaknesses),
        "opportunities": opportunities,
        "threats": tuple(threats),
        "source_proven": len(strengths),
        "source_unresolved": len(weaknesses),
        "protocol_receipt_chain_verified": (
            protocol.get("receipt_chain_verified") is True
        ),
        "live_operations_verified": False,
        "read_only": True,
        "independent_agent_votes_claimed": False,
        "execution_granted": False,
        "founder_final_required": True,
        "full_green": False,
    }


def readiness_signals() -> dict[str, dict[str, str]]:
    """Report only readback-backed readiness, never an assumed software Green.

    A loaded source module proves code presence, not CI, approval or production.
    The shared organism worker's durable heartbeat does not prove that a
    Company Intelligence agent executed a business task.
    """
    worker_state = "UNKNOWN"
    worker_reference = ""
    worker_note = "No fresh durable organism-worker heartbeat verified."
    try:
        worker = organism_runtime.runtime_status()
    except Exception:  # noqa: BLE001 - unavailable readiness must fail closed.
        worker = {}
    if (
        isinstance(worker, dict)
        and worker.get("schema_ready") is True
        and worker.get("worker_fresh") is True
        and worker.get("ready") is True
        and not worker.get("error")
    ):
        worker_state = "PROVEN"
        worker_reference = "oap:organism-runtime:postgres:worker-heartbeat"
        worker_note = (
            "Fresh organism worker heartbeat; Company Intelligence task "
            "execution remains unverified."
        )
    return {
        "code_present": {
            "state": "PRESENT",
            "evidence_reference": "oap:company-intelligence:loaded-runtime-projection",
            "note": "This projection executed; code presence is not deployment readiness.",
        },
        "ci_verified": {
            "state": "UNKNOWN",
            "evidence_reference": "",
            "note": "No exact-head CI receipt is bound to this runtime request.",
        },
        "worker_connected": {
            "state": worker_state,
            "evidence_reference": worker_reference,
            "note": worker_note,
        },
        "guardian_hrm_verified": {
            "state": "UNKNOWN",
            "evidence_reference": "",
            "note": "No request-bound Guardian, HRM and Human Authority receipt verified.",
        },
        "production_verified": {
            "state": "UNKNOWN",
            "evidence_reference": "",
            "note": "No verified production deployment and session proof supplied.",
        },
    }

def projection(identity_id: str) -> dict[str, Any]:
    items: list[dict[str, str]] = [_company_registry_item()]
    items.extend(_music_items(identity_id))
    items.extend(_commerce_items(identity_id))
    snapshot = company_evidence_ingestion.ingest_snapshot(items)
    try:
        protocol_registry = (
            company_intelligence_evidence_store.CompanyIntelligenceEvidenceStore()
            .projection(owner_identity_id=identity_id)
        )
    except company_intelligence_evidence_store.CompanyIntelligenceEvidenceUnavailable:
        protocol_registry = {
            **company_intelligence_evidence_registry.snapshot(),
            "receipt_chain_verified": False,
            "receipt_count": 0,
            "head_hash": company_intelligence_evidence_store.GENESIS_HASH,
            "store_fail_closed": True,
            "store_unavailable": True,
        }
    department_snapshot = department_map(
        snapshot, protocol_proven_count=protocol_registry["proven_count"],
    )
    swot_snapshot = swot_first_review(
        snapshot, department_snapshot, protocol_registry,
    )
    readiness = readiness_signals()
    return {
        "name": "OAP Company Intelligence",
        "readiness": readiness,
        "evidence": snapshot,
        "evidence_items": tuple(items),
        "protocol_registry": protocol_registry,
        "swot_first": swot_snapshot,
        "department_map": department_snapshot,
        "protocol_check_count": protocol_registry["protocol_check_count"],
        "protocol_proven_count": protocol_registry["proven_count"],
        "protocol_green_gate_passed": protocol_registry["green_gate_passed"],
        "protocol_receipt_chain_verified": protocol_registry.get(
            "receipt_chain_verified", False
        ),
        "protocol_receipt_count": protocol_registry.get("receipt_count", 0),
        "proven_count": len(snapshot["proven_domains"]),
        "domain_count": snapshot["domain_count"],
        "evidence_percentage": round(
            (len(snapshot["proven_domains"]) / snapshot["domain_count"]) * 100, 1
        ),
        "source_evidence_complete": snapshot["all_domains_proven"],
        "operational_green": False,
        "founder_final_required": True,
        "full_green": False,
        "truth_boundary": (
            "Code presence, CI, worker health, governance and production proof "
            "are separate. "
            "No missing or conflicting external proof is promoted to Green."
        ),
    }
