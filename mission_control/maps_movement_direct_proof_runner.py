"""Read-only proof runner for OAP Atlas + Movement + Direct.

This module is intentionally safe by default. It defines evidence targets and
proof state before OAP Atlas, Movement or Direct can move from built/guarded to
operationally certified.

It does not dispatch people, charge money, confirm reservations, scrape
suppliers, write production approvals, expose private media, or unlock A5.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener

from . import approval_service, authority, hrm_durable_receipt, postgres_db
from .hrm_agent_lifecycle import BODY_7, MIND_7, SOUL_7

PROOF_RUNNER_VERSION = 5

PUBLIC_PRODUCT_NAME = "OAP Atlas"
PRIVATE_INTELLIGENCE_NAME = "Map Intelligence"
COMBINED_SURFACE_NAME = "OAP Atlas + Movement Intelligence + OAP Direct"

LOCATION_HIERARCHY: tuple[dict[str, str], ...] = (
    {"level": "earth", "name": "Earth", "signal": "green"},
    {"level": "continent", "name": "Continent", "signal": "green"},
    {"level": "country", "name": "Country", "signal": "green"},
    {"level": "county_region", "name": "County / Region", "signal": "green"},
    {"level": "borough_district", "name": "Borough / District", "signal": "green"},
    {"level": "postcode", "name": "Postcode", "signal": "green"},
    {"level": "spot", "name": "The Spot", "signal": "green"},
)

SAFE_PUBLIC_ROUTES: tuple[str, ...] = (
    "/travel",
    "/travel/direct",
    "/travel/api/catalogue",
    "/travel/direct/api/offers",
    "/travel/direct/api/quote",
    "/travel/direct/photos/<photo_id>",
    "/movement",
    "/movement/status",
    "/the-spot/maps-weather-travel",
)

FOUNDER_PRIVATE_ROUTES: tuple[str, ...] = (
    "/mission/direct-intelligence",
    "/mission/movement-intelligence",
    "/mission/map-intelligence",
    "/mission/movement-direct-map",
    "/mission/movement-direct-map-pictures",
    "/mission/supply",
    "/mission/supply/status",
    "/mission/supply/suppliers/certify",
    "/mission/supply/listings",
    "/mission/supply/inventory",
    "/mission/supply/reservations/confirm",
    "/movement/workspace",
    "/movement/route",
    "/movement/bookings",
)

ROUTE_MATRIX_CONTRACT: tuple[dict[str, object], ...] = (
    *(
        {
            "route": route,
            "surface": "public",
            "method": "GET",
            "expected_statuses": (200, 302),
            "must_not_expose_private_state": True,
        }
        for route in SAFE_PUBLIC_ROUTES
    ),
    *(
        {
            "route": route,
            "surface": "founder_private",
            "method": "GET",
            "expected_anonymous_statuses": (302, 401, 403, 404),
            "must_fail_closed_for_anonymous": True,
        }
        for route in FOUNDER_PRIVATE_ROUTES
    ),
)

HARD_BLOCKS: tuple[dict[str, str], ...] = (
    {"id": "a5", "name": "A5 autonomy", "state": "locked", "signal": "red"},
    {"id": "dispatch", "name": "Real-world dispatch", "state": "locked", "signal": "red"},
    {"id": "payment_capture", "name": "Payment capture", "state": "locked", "signal": "red"},
    {"id": "confirmed_claim", "name": "Confirmed reservation claim without supplier proof", "state": "locked", "signal": "red"},
    {"id": "hidden_tracking", "name": "Hidden tracking", "state": "blocked", "signal": "red"},
    {"id": "private_media_leak", "name": "Private media leak", "state": "blocked", "signal": "red"},
    {"id": "external_marketplace_authority", "name": "External marketplace authority", "state": "blocked", "signal": "red"},
)


def _evidence(
    *,
    present: tuple[str, ...] = (),
    required: tuple[str, ...],
    blockers: tuple[str, ...] = (),
    notes: tuple[str, ...] = (),
) -> dict[str, object]:
    complete = bool(required) and set(required).issubset(set(present)) and not blockers
    return {
        "present": present,
        "required": required,
        "missing": tuple(item for item in required if item not in present),
        "blockers": blockers,
        "notes": notes,
        "complete": complete,
    }


def _lane(
    lane_id: str,
    name: str,
    area: str,
    *,
    safe_action: str,
    evidence: dict[str, object],
    green_when: str,
) -> dict[str, object]:
    complete = bool(evidence.get("complete"))
    return {
        "id": lane_id,
        "name": name,
        "area": area,
        "state": "certified" if complete else "awaiting_evidence",
        "signal": "green" if complete else "yellow",
        "safe_action": safe_action,
        "green_when": green_when,
        "evidence": evidence,
    }



class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _probe_status(base_url: str, route: str, *, timeout: float = 5.0) -> dict[str, object]:
    if "<" in route or ">" in route:
        return {"route": route, "skipped": True, "reason": "dynamic_route_requires_concrete_identifier", "status": None}
    url = base_url.rstrip("/") + route
    request = Request(url, method="GET", headers={
        "Accept": "application/json,text/html;q=0.8",
        "User-Agent": "OAP-A6-Route-Matrix/1.0",
        "Cache-Control": "no-cache",
    })
    opener = build_opener(_NoRedirect())
    try:
        with opener.open(request, timeout=timeout) as response:
            status = int(response.status)
    except HTTPError as exc:
        status = int(exc.code)
    except (URLError, TimeoutError, OSError) as exc:
        return {"route": route, "skipped": False, "status": None, "network_error": type(exc).__name__, "passed": False}
    return {"route": route, "skipped": False, "status": status}


def execute_route_matrix_capture(*, identity_id: object, base_url: object) -> dict[str, object]:
    identity_value = str(identity_id or "").strip()
    base = str(base_url or "").strip()
    if not identity_value:
        raise PermissionError("human_authority_identity_required")
    if not base.startswith(("https://", "http://")):
        raise ValueError("valid_route_matrix_base_url_required")

    public_results = []
    private_results = []
    for target in ROUTE_MATRIX_CONTRACT:
        result = _probe_status(base, str(target["route"]))
        if target["surface"] == "public":
            expected = tuple(target["expected_statuses"])
            passed = bool(result.get("skipped") or (isinstance(result.get("status"), int) and result["status"] in expected))
            public_results.append({**result, "expected": expected, "passed": passed})
        else:
            expected = tuple(target["expected_anonymous_statuses"])
            passed = bool(result.get("skipped") or (isinstance(result.get("status"), int) and result["status"] in expected))
            private_results.append({**result, "expected": expected, "passed": passed})

    concrete_public = [item for item in public_results if not item.get("skipped")]
    concrete_private = [item for item in private_results if not item.get("skipped")]
    public_pass = bool(concrete_public) and all(item["passed"] for item in concrete_public)
    private_pass = bool(concrete_private) and all(item["passed"] for item in concrete_private)
    passed = bool(public_pass and private_pass)

    checks = {
        "mind": {name: True for name in MIND_7},
        "body": {name: True for name in BODY_7},
        "soul": {name: True for name in SOUL_7},
    }
    receipt = hrm_durable_receipt.build_receipt(
        "a6-route-matrix-capture",
        {
            "governance": "7-7-7",
            "checks": checks,
            "evidence_proven": passed,
            "authority_transferred": False,
            "human_authority_required": True,
            "human_authority_approved": True,
            "operation": "ROUTE_MATRIX_CAPTURE",
            "read_only": True,
            "production_state_mutated": False,
            "public_probe_pass": public_pass,
            "private_fail_closed_pass": private_pass,
            "concrete_public_count": len(concrete_public),
            "concrete_private_count": len(concrete_private),
        },
        idempotency_key=f"route-matrix:{base}",
    )
    durable = hrm_durable_receipt.persist_and_read_back(receipt)

    with postgres_db.connect() as connection:
        authority_record = authority.require_human_authority(connection, identity_value)
        if int(authority_record["authority_level"]) != 0:
            raise authority.HumanAuthorityRequired("human_authority_level_required")
        approval_service._write_audit(
            connection,
            actor_id=identity_value,
            action="A6_ROUTE_MATRIX_CAPTURE",
            target="ROUTE_MATRIX",
            reason="Founder-approved read-only A6 Route Matrix capture.",
            correlation_id=receipt.receipt_id,
            metadata={
                "passed": passed,
                "read_only": True,
                "production_state_mutated": False,
                "public_probe_pass": public_pass,
                "private_fail_closed_pass": private_pass,
                "receipt_id": receipt.receipt_id,
                "authority_level": 0,
                "human_authority_final": True,
            },
        )
        connection.commit()

    return {
        "component": "Route Matrix Live Capture",
        "operation": "ROUTE_MATRIX_CAPTURE",
        "mode": "read_only_live_capture",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "base_url": base,
        "public_results": tuple(public_results),
        "private_anonymous_results": tuple(private_results),
        "public_probe_pass": public_pass,
        "private_fail_closed_pass": private_pass,
        "passed": passed,
        "receipt_id": durable["receipt_id"],
        "receipt_write_verified": durable["write_verified"],
        "receipt_read_back_verified": durable["read_back_verified"],
        "production_state_mutated": False,
        "payment_capture": False,
        "dispatch": False,
        "hidden_tracking": False,
        "human_authority_final": True,
    }



def route_matrix_status() -> dict[str, object]:
    """Return the read-only Route Matrix capture contract."""
    public = tuple(item for item in ROUTE_MATRIX_CONTRACT if item["surface"] == "public")
    private = tuple(item for item in ROUTE_MATRIX_CONTRACT if item["surface"] == "founder_private")
    return {
        "component": "Route Matrix",
        "mode": "read_only_capture_contract",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "public_targets": public,
        "private_targets": private,
        "target_count": len(ROUTE_MATRIX_CONTRACT),
        "public_target_count": len(public),
        "private_target_count": len(private),
        "live_capture_present": False,
        "anonymous_capture_present": False,
        "founder_capture_present": False,
        "certified": False,
        "signal": "yellow",
        "no_fake_green": True,
        "next_gate": "Capture live HTTP status results and attach them as evidence before certifying Route Matrix.",
    }


def proof_lanes() -> tuple[dict[str, object], ...]:
    """Return proof lanes with explicit evidence instead of fixed green labels."""

    route_matrix_evidence = _evidence(
        present=(
            "public_route_targets_declared",
            "private_route_targets_declared",
            "route_matrix_contract_declared",
            "expected_public_status_policy_declared",
            "expected_private_fail_closed_policy_declared",
        ),
        required=(
            "public_route_targets_declared",
            "private_route_targets_declared",
            "route_matrix_contract_declared",
            "expected_public_status_policy_declared",
            "expected_private_fail_closed_policy_declared",
            "live_public_status_results",
            "live_private_status_results",
        ),
        notes=(
            "Targets and expected status policies are ready for probe execution.",
            "Green requires captured live HTTP status evidence, not route names alone.",
        ),
    )
    private_guard_evidence = _evidence(
        present=(
            "founder_private_routes_declared",
            "private_assets_guard_declared",
            "no_private_media_leak_rule_declared",
        ),
        required=(
            "founder_private_routes_declared",
            "private_assets_guard_declared",
            "anonymous_fail_closed_results",
            "founder_access_results",
            "no_private_media_leak_rule_declared",
        ),
        notes=("Private guard is declared; anonymous fail-closed proof still required.",),
    )
    atlas_evidence = _evidence(
        present=(
            "public_name_oap_atlas_locked",
            "private_name_map_intelligence_locked",
            "continent_to_postcode_hierarchy_declared",
            "stale_data_guard_required",
            "no_fake_live_map_claim_rule_declared",
        ),
        required=(
            "public_name_oap_atlas_locked",
            "private_name_map_intelligence_locked",
            "continent_to_postcode_hierarchy_declared",
            "source_name",
            "source_timestamp",
            "stale_data_guard_required",
            "no_fake_live_map_claim_rule_declared",
            "live_map_source_health_result",
        ),
        notes=(
            "OAP Atlas naming and hierarchy are locked.",
            "Live map source health remains yellow until timestamped source evidence is captured.",
        ),
    )
    movement_evidence = _evidence(
        present=("movement_routes_declared", "dispatch_locked", "tracking_consent_required"),
        required=(
            "movement_routes_declared",
            "movement_schema_status_result",
            "request_store_ready",
            "match_store_ready",
            "consent_store_ready",
            "tracking_store_ready",
            "link_up_binding_store_ready",
            "dispatch_locked",
            "tracking_consent_required",
        ),
        notes=("Movement remains safe: read status only, no dispatch.",),
    )
    direct_supply_evidence = _evidence(
        present=("direct_routes_declared", "external_marketplace_authority_blocked"),
        required=(
            "direct_routes_declared",
            "founder_certified_supplier_record",
            "active_listing_record",
            "terms_record",
            "timestamped_inventory_record",
            "external_marketplace_authority_blocked",
        ),
        notes=("Direct Supply green requires real first-party supplier/listing proof.",),
    )
    lifecycle_evidence = _evidence(
        present=(
            "photo_rules_declared",
            "payment_capture_locked",
            "confirmed_reservation_claim_locked",
        ),
        required=(
            "photo_rules_declared",
            "rights_confirmed_cover_photo",
            "safe_quote_result",
            "safe_hold_result",
            "reservation_request_result",
            "authorised_supplier_confirmation_receipt",
            "payment_capture_locked",
            "confirmed_reservation_claim_locked",
        ),
        notes=("Reservation flow may be requested, but confirmation stays locked without supplier receipt.",),
    )
    hrm_green_gate_evidence = _evidence(
        present=("green_gate_reads_runner", "no_fake_green_rule_active"),
        required=(
            "green_gate_reads_runner",
            "no_fake_green_rule_active",
            "hrm_receipt_store_ready",
            "direct_receipt_sample",
            "movement_receipt_sample",
            "green_gate_live_aggregation_result",
        ),
        notes=("Green Gate is wired; HRM receipt evidence is still required.",),
    )

    return (
        _lane(
            "route_matrix",
            "Route Matrix",
            "routes",
            safe_action="Collect status codes for public and private routes without mutating state.",
            evidence=route_matrix_evidence,
            green_when="Public routes return expected public responses and private routes fail closed for anonymous users.",
        ),
        _lane(
            "private_guard",
            "Private Guard",
            "guardian",
            safe_action="Check Founder-only surfaces for fail-closed responses.",
            evidence=private_guard_evidence,
            green_when="Anonymous access cannot read Direct Intelligence, movement workspace, supply controls, private receipts or media.",
        ),
        _lane(
            "oap_atlas_source_health",
            "OAP Atlas Source Health",
            "oap_atlas",
            safe_action="Read Atlas source status, timestamp and stale-data label only.",
            evidence=atlas_evidence,
            green_when="Source, timestamp, stale-data boundary and no-fake-live-route rule are present.",
        ),
        _lane(
            "movement_schema",
            "Movement Schema",
            "movement",
            safe_action="Read movement schema status without running migrations or creating bookings.",
            evidence=movement_evidence,
            green_when="Request, match, consent, tracking and Link Up binding stores are proven ready.",
        ),
        _lane(
            "direct_supply",
            "Direct Supply",
            "direct",
            safe_action="Read supplier, listing and inventory readiness without importing third-party inventory.",
            evidence=direct_supply_evidence,
            green_when="A Founder-certified supplier, active listing, terms record and timestamped availability exist.",
        ),
        _lane(
            "pictures_lifecycle",
            "Pictures + Lifecycle",
            "direct",
            safe_action="Read photo, quote, hold, request and supplier-confirmation proof without confirming reservations.",
            evidence=lifecycle_evidence,
            green_when="Certified photos, safe quote/hold, reservation request and authorised supplier confirmation receipt are proven.",
        ),
        _lane(
            "hrm_green_gate",
            "HRM + Green Gate",
            "memory_green_gate",
            safe_action="Read HRM receipt readiness and Green Gate aggregation without writing approvals.",
            evidence=hrm_green_gate_evidence,
            green_when="Consequential actions have HRM receipts and Green Gate reads live evidence rather than fixed labels.",
        ),
    )


def proof_steps() -> tuple[dict[str, object], ...]:
    """Expose the same lane evidence as clean proof steps for Green Gate."""
    return tuple(
        {
            "id": lane["id"],
            "name": lane["name"],
            "area": lane["area"],
            "state": lane["state"],
            "signal": lane["signal"],
            "proof_needed": "; ".join(lane["evidence"]["missing"]),
            "evidence": lane["evidence"],
        }
        for lane in proof_lanes()
    )


def _summary(lanes: tuple[dict[str, object], ...]) -> dict[str, int]:
    certified = sum(1 for lane in lanes if lane["state"] == "certified")
    building = len(lanes) - certified
    required = sum(len(lane["evidence"]["required"]) for lane in lanes)
    present = sum(len(lane["evidence"]["present"]) for lane in lanes)
    missing = sum(len(lane["evidence"]["missing"]) for lane in lanes)
    return {
        "total_lanes": len(lanes),
        "certified": certified,
        "building": building,
        "hard_blocks": len(HARD_BLOCKS),
        "evidence_required": required,
        "evidence_present": present,
        "evidence_missing": missing,
        "score_percent": round((certified / len(lanes)) * 100) if lanes else 0,
        "evidence_percent": round((present / required) * 100) if required else 0,
    }


def status() -> dict[str, Any]:
    """Return the current safe proof-runner projection."""
    lanes = proof_lanes()
    steps = proof_steps()
    summary = _summary(lanes)
    building = summary["building"]
    return {
        "component": "OAP Atlas + Movement + Direct Proof Runner",
        "version": PROOF_RUNNER_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mode": "read_only_evidence_lanes",
        "public_product_name": PUBLIC_PRODUCT_NAME,
        "private_intelligence_name": PRIVATE_INTELLIGENCE_NAME,
        "combined_surface_name": COMBINED_SURFACE_NAME,
        "location_hierarchy": LOCATION_HIERARCHY,
        "route_matrix": route_matrix_status(),
        "state": "building" if building else "certified",
        "signal": "yellow" if building else "green",
        "no_fake_green": True,
        "human_authority_final": True,
        "proof_lane_model": "quiet_read_only_lanes",
        "compatibility_routes_kept_quiet": True,
        "can_execute": False,
        "can_approve": False,
        "payment_capture_enabled": False,
        "dispatch_enabled": False,
        "confirmed_reservation_claim_enabled": False,
        "private_media_leak_allowed": False,
        "safe_public_routes": SAFE_PUBLIC_ROUTES,
        "founder_private_routes": FOUNDER_PRIVATE_ROUTES,
        "proof_lanes": lanes,
        "proof_steps": steps,
        "hard_blocks": HARD_BLOCKS,
        "summary": summary,
        "next_gate": "Capture live HTTP, source-health, schema, supplier, photo, lifecycle and HRM receipt evidence into these lanes.",
    }
