"""OAP 777 signal and seven-star advisory rating contract.

Caller must supply authenticated evidence from existing Guardian/HRM systems.
Receipt IDs alone are NOT proof. No live ratings or promotions are issued here.
"""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

SIGNALS = ("execution", "reliability", "intelligence", "collaboration",
           "innovation", "integrity", "memory")
VALID = ("GREEN", "AMBER", "RED", "UNKNOWN")

def signal_rating(
    signals: Mapping[str, Mapping[str, Any]],
    *,
    evidence_authenticated: bool = False,
    safety_cleared: bool = False,
) -> dict[str, Any]:
    """Return advisory score only when every signal has authenticated evidence.

    Values 0..100 and a nonempty receipt reference are inputs from the caller;
    this function cannot authenticate them. A RED integrity signal blocks.
    """
    if set(signals) != set(SIGNALS):
        raise ValueError("exactly seven signals required")
    normalized: dict[str, dict[str, Any]] = {}
    all_proven = evidence_authenticated
    for name in SIGNALS:
        record = signals[name]
        status = record.get("status")
        value = record.get("value")
        receipt = record.get("receipt_id")
        if status not in VALID:
            raise ValueError("invalid signal status")
        valid_score = (
            isinstance(value, (int, float)) and not isinstance(value, bool)
            and 0 <= value <= 100
        )
        proven = (status != "UNKNOWN" and valid_score
                  and isinstance(receipt, str) and bool(receipt.strip())
                  and evidence_authenticated)
        all_proven = all_proven and proven
        normalized[name] = {
            "status": status,
            "score": float(value) if proven else None,
            "receipt_id": receipt if proven else None,
            "verified": bool(proven),
        }
    safety_blocked = (normalized["integrity"]["status"] == "RED"
                      or not safety_cleared)
    if all_proven:
        average = sum(normalized[k]["score"] for k in SIGNALS) / len(SIGNALS)
        stars = round(average * 7 / 100, 2)
    else:
        average = None
        stars = None
    return {
        "mode": "advisory_only",
        "signals": normalized,
        "seven_star_rating": stars,
        "average_score": round(average, 2) if average is not None else None,
        "promotion_gate": "REVIEW" if all_proven and not safety_blocked else "HOLD",
        "badge_issued": False,
        "authority_granted": False,
        "authenticity_verified_by_module": False,
    }
