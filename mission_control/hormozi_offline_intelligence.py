"""Offline-first Hormozi commercial intelligence for OAP Company Intelligence.

Runs entirely from supplied/local OAP data. It never fetches live market data,
publishes offers, changes prices, captures payments, or grants legal/regulatory
authority. Stale or missing evidence remains explicit.
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping

FRESHNESS_STATES = ("FRESH", "ACCEPTABLE", "STALE", "EXPIRED", "UNKNOWN")
EPISTEMIC_STATES = ("VERIFIED", "SUPPORTED", "INFERRED", "ESTIMATED", "STALE", "UNKNOWN")
HORMOZI_LENSES = (
    "dream_outcome",
    "perceived_likelihood",
    "time_delay",
    "effort_sacrifice",
    "offer_stack",
    "price_value_gap",
    "unit_economics",
)


def _decimal(value: object, name: str) -> Decimal:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"invalid_{name}") from exc
    if result < 0:
        raise ValueError(f"invalid_{name}")
    return result


def _timestamp(value: object) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def freshness_state(
    observed_at: object,
    *,
    now: object = None,
    acceptable_hours: int = 72,
    stale_hours: int = 168,
    expired_hours: int = 720,
) -> str:
    observed = _timestamp(observed_at)
    current = _timestamp(now) if now else datetime.now(timezone.utc)
    if observed is None or current is None or observed > current:
        return "UNKNOWN"
    age_hours = (current - observed).total_seconds() / 3600
    if age_hours <= acceptable_hours:
        return "FRESH"
    if age_hours <= stale_hours:
        return "ACCEPTABLE"
    if age_hours <= expired_hours:
        return "STALE"
    return "EXPIRED"


def unit_economics(offer: Mapping[str, object]) -> dict[str, object]:
    price = _decimal(offer.get("price", 0), "price")
    direct = _decimal(offer.get("direct_cost", 0), "direct_cost")
    fulfilment = _decimal(offer.get("fulfilment_cost", 0), "fulfilment_cost")
    payment = _decimal(offer.get("payment_cost", 0), "payment_cost")
    refund_allowance = _decimal(
        offer.get("refund_allowance", 0),
        "refund_allowance",
    )
    total_cost = direct + fulfilment + payment + refund_allowance
    contribution = price - total_cost
    margin_pct = (
        (contribution / price * Decimal("100")) if price > 0 else Decimal("0")
    )
    return {
        "price": float(price),
        "total_cost": float(total_cost),
        "contribution_margin": float(contribution),
        "contribution_margin_percentage": round(float(margin_pct), 2),
        "positive_contribution": contribution > 0,
    }


def evaluate_offer(
    offer: Mapping[str, object],
    *,
    now: object = None,
) -> dict[str, Any]:
    """Evaluate one locally available offer without live external assumptions."""

    economics = unit_economics(offer)
    evidence = tuple(offer.get("evidence") or ())
    deliverables = tuple(offer.get("deliverables") or ())
    onboarding_steps = int(offer.get("onboarding_steps", 0) or 0)
    delivery_hours = int(offer.get("delivery_hours", 0) or 0)
    evidence_observed_at = offer.get("evidence_observed_at")
    freshness = freshness_state(evidence_observed_at, now=now)

    evidence_count = len([item for item in evidence if str(item).strip()])
    deliverable_count = len([item for item in deliverables if str(item).strip()])
    external_current_required = bool(offer.get("requires_live_external_data", False))

    scores = {
        "dream_outcome": 100 if str(offer.get("customer_outcome") or "").strip() else 0,
        "perceived_likelihood": min(100, evidence_count * 20),
        "time_delay": 100 if 0 < delivery_hours <= 24 else 70 if delivery_hours <= 72 else 40,
        "effort_sacrifice": 100 if onboarding_steps <= 2 else 70 if onboarding_steps <= 5 else 40,
        "offer_stack": min(100, deliverable_count * 20),
        "price_value_gap": 80 if deliverable_count >= 3 and economics["positive_contribution"] else 50,
        "unit_economics": 100 if economics["positive_contribution"] else 0,
    }
    overall = round(sum(scores.values()) / len(scores), 1)

    blockers: list[str] = []
    if freshness in {"STALE", "EXPIRED", "UNKNOWN"}:
        blockers.append("evidence_freshness")
    if external_current_required:
        blockers.append("live_external_verification_required")
    if not economics["positive_contribution"]:
        blockers.append("non_positive_contribution_margin")
    if not str(offer.get("customer_outcome") or "").strip():
        blockers.append("customer_outcome_missing")

    recommendations: list[str] = []
    if scores["perceived_likelihood"] < 80:
        recommendations.append("strengthen_delivery_evidence")
    if scores["offer_stack"] < 80:
        recommendations.append("clarify_or_strengthen_offer_stack")
    if scores["effort_sacrifice"] < 80:
        recommendations.append("reduce_customer_onboarding_friction")
    if scores["time_delay"] < 80:
        recommendations.append("reduce_time_to_first_value")
    if not economics["positive_contribution"]:
        recommendations.append("repair_unit_economics_before_publishing")

    live_safe = not blockers
    epistemic = (
        "VERIFIED"
        if live_safe and evidence_count > 0 and freshness in {"FRESH", "ACCEPTABLE"}
        else "STALE"
        if freshness in {"STALE", "EXPIRED"}
        else "SUPPORTED"
        if evidence_count > 0
        else "UNKNOWN"
    )
    return {
        "engine": "OAP Offline Hormozi Intelligence",
        "offer_id": str(offer.get("offer_id") or "").strip(),
        "offline_capable": True,
        "network_required_for_analysis": False,
        "lenses": scores,
        "overall_score": overall,
        "unit_economics": economics,
        "freshness": freshness,
        "epistemic_state": epistemic,
        "blockers": tuple(blockers),
        "recommendations": tuple(recommendations),
        "commercial_change_ready": live_safe,
        "automatic_publish_allowed": False,
        "automatic_price_change_allowed": False,
        "payment_capture_allowed": False,
        "external_claims_allowed": False,
        "founder_final_required": True,
    }


def scenario_compare(
    offer: Mapping[str, object],
    scenarios: tuple[Mapping[str, object], ...],
    *,
    now: object = None,
) -> dict[str, Any]:
    """Compare local what-if scenarios without changing the source offer."""

    baseline = evaluate_offer(offer, now=now)
    results: list[dict[str, Any]] = []
    for index, changes in enumerate(scenarios[:10], start=1):
        candidate = dict(offer)
        candidate.update(dict(changes))
        evaluation = evaluate_offer(candidate, now=now)
        results.append({
            "scenario_id": f"scenario-{index}",
            "changes": dict(changes),
            "overall_score": evaluation["overall_score"],
            "unit_economics": evaluation["unit_economics"],
            "blockers": evaluation["blockers"],
        })
    return {
        "baseline": baseline,
        "scenarios": tuple(results),
        "source_offer_mutated": False,
        "simulation_is_not_runtime_proof": True,
        "founder_final_required": True,
    }


def local_receipt(
    evaluation: Mapping[str, object],
    *,
    created_at: object = None,
) -> dict[str, object]:
    timestamp = _timestamp(created_at) or datetime.now(timezone.utc)
    payload = {
        "engine": str(evaluation.get("engine") or ""),
        "offer_id": str(evaluation.get("offer_id") or ""),
        "overall_score": evaluation.get("overall_score"),
        "freshness": str(evaluation.get("freshness") or "UNKNOWN"),
        "epistemic_state": str(evaluation.get("epistemic_state") or "UNKNOWN"),
        "blockers": tuple(evaluation.get("blockers") or ()),
        "recommendations": tuple(evaluation.get("recommendations") or ()),
        "created_at": timestamp.isoformat(),
    }
    digest = hashlib.sha256(
        json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    return {
        **payload,
        "receipt_sha256": digest,
        "sync_state": "LOCAL_PENDING",
        "authorises_external_action": False,
        "founder_final_required": True,
    }


def reconcile(
    local_receipt_row: Mapping[str, object],
    remote_state: Mapping[str, object],
) -> dict[str, object]:
    """Fail closed when later connected data conflicts with offline evidence."""

    local_offer = str(local_receipt_row.get("offer_id") or "")
    remote_offer = str(remote_state.get("offer_id") or "")
    conflicts: list[str] = []
    if local_offer and remote_offer and local_offer != remote_offer:
        conflicts.append("offer_identity")
    local_freshness = str(local_receipt_row.get("freshness") or "UNKNOWN")
    remote_freshness = str(remote_state.get("freshness") or "UNKNOWN")
    if remote_freshness in {"FRESH", "ACCEPTABLE"} and local_freshness in {"STALE", "EXPIRED", "UNKNOWN"}:
        conflicts.append("newer_remote_evidence")
    if (
        "unit_economics" in remote_state
        and remote_state.get("unit_economics") != local_receipt_row.get("unit_economics")
    ):
        conflicts.append("unit_economics")

    return {
        "coherent": not conflicts,
        "conflicts": tuple(conflicts),
        "resolution": "sync_allowed" if not conflicts else "human_review_required",
        "silent_overwrite_allowed": False,
        "automatic_external_action_allowed": False,
        "founder_final_required": True,
    }


def status() -> dict[str, object]:
    return {
        "name": "OAP Offline Hormozi Intelligence",
        "lens_count": len(HORMOZI_LENSES),
        "offline_first": True,
        "network_required_for_analysis": False,
        "freshness_states": FRESHNESS_STATES,
        "epistemic_states": EPISTEMIC_STATES,
        "scenario_analysis": True,
        "local_receipts": True,
        "sync_later_reconciliation": True,
        "automatic_publish_allowed": False,
        "automatic_price_change_allowed": False,
        "payment_capture_allowed": False,
        "human_authority_final": True,
    }
