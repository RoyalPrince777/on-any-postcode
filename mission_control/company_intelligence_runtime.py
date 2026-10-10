"""Live read-only evidence projection for OAP Company Intelligence.

This layer reuses existing OAP Music and Market stores. It never invents evidence:
missing rows, unavailable stores, incomplete rights receipts, or missing margin proof
remain UNKNOWN/CONFLICTING rather than becoming Green.
"""
from __future__ import annotations

import os
from datetime import datetime, UTC
from typing import Any

from . import (
    company_evidence_ingestion,
    market_supplier_network,
    music_evidence,
    product_core_services,
)

_COMPANY_NUMBER = "14753133"
_COMPANY_SOURCE = (
    "https://find-and-update.company-information.service.gov.uk/company/14753133"
)


def _now() -> str:
    return datetime.now(UTC).isoformat()


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


def projection(identity_id: str) -> dict[str, Any]:
    items: list[dict[str, str]] = [_company_registry_item()]
    items.extend(_music_items(identity_id))
    items.extend(_commerce_items(identity_id))
    snapshot = company_evidence_ingestion.ingest_snapshot(items)
    software_green = True
    return {
        "name": "OAP Company Intelligence",
        "software_green": software_green,
        "evidence": snapshot,
        "evidence_items": tuple(items),
        "proven_count": len(snapshot["proven_domains"]),
        "domain_count": snapshot["domain_count"],
        "evidence_percentage": round(
            (len(snapshot["proven_domains"]) / snapshot["domain_count"]) * 100, 1
        ),
        "operational_green": snapshot["all_domains_proven"],
        "founder_final_required": True,
        "full_green": False,
        "truth_boundary": (
            "Software readiness and evidence readiness are separate. "
            "No missing or conflicting external proof is promoted to Green."
        ),
    }
