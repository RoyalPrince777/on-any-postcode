"""Canonical evidence-backed SMI mission status for OAP Library."""
from __future__ import annotations

from typing import Any


CHECKS: tuple[dict[str, Any], ...] = (
    {"id": "library_front_door", "label": "Library front door", "passed": True},
    {"id": "books_route", "label": "Books route", "passed": True},
    {"id": "my_library", "label": "Owner-scoped My Library", "passed": True},
    {"id": "reader", "label": "Protected ebook reader", "passed": True},
    {"id": "entitlements", "label": "Verified entitlement projection", "passed": True},
    {"id": "creator_drafts", "label": "Durable creator drafts", "passed": True},
    {"id": "creator_review", "label": "Rights-attested review submission", "passed": True},
    {"id": "market_bridge", "label": "Approved ebook to Market bridge", "passed": True},
    {"id": "product_page", "label": "Public ebook product page", "passed": False},
    {"id": "unlock", "label": "Unlock / checkout intent", "passed": False},
    {"id": "payment_verification", "label": "Independent captured-payment verification", "passed": False},
    {"id": "entitlement_issuance", "label": "Payment to entitlement issuance", "passed": False},
    {"id": "refund_revocation", "label": "Refund / revocation lifecycle", "passed": False},
    {"id": "production_schema", "label": "Production schema installation proof", "passed": False},
)


def status() -> dict[str, Any]:
    passed = sum(1 for item in CHECKS if item["passed"])
    total = len(CHECKS)
    return {
        "mission": "OAP Library digital release",
        "mode": "SMI_AUTO",
        "truth_mode": True,
        "upgrade_only": True,
        "physical_scope_excluded": True,
        "checks": CHECKS,
        "passed": passed,
        "total": total,
        "evidence_percentage": round((passed / total) * 100),
        "software_release_candidate": True,
        "ci_green": True,
        "runtime_image_green": True,
        "governed_checks_green": True,
        "live_payment_claimed": False,
        "production_green": False,
        "next_blocker": (
            "Public ebook product page -> Unlock -> independently verified captured "
            "payment -> durable entitlement -> Owned -> refund/revocation proof."
        ),
        "human_authority_final": True,
    }
