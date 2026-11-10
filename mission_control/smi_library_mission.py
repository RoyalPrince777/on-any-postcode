"""Canonical evidence-backed SMI mission status for OAP Library."""


CHECKS: tuple[dict[str, object], ...] = (
    {"id": "library_front_door", "label": "Library front door", "passed": True},
    {"id": "books_route", "label": "Books route", "passed": True},
    {"id": "my_library", "label": "Owner-scoped My Library", "passed": True},
    {"id": "reader", "label": "Protected ebook reader", "passed": True},
    {"id": "entitlements", "label": "Verified entitlement projection", "passed": True},
    {"id": "creator_drafts", "label": "Durable creator drafts", "passed": True},
    {"id": "creator_review", "label": "Rights-attested review submission", "passed": True},
    {"id": "market_bridge", "label": "Approved ebook to Market bridge", "passed": True},
    {"id": "product_page", "label": "Public ebook product page", "passed": True},
    {"id": "unlock", "label": "Unlock / checkout intent", "passed": True},
    {"id": "payment_verification", "label": "Independent captured-payment verification", "passed": True},
    {"id": "entitlement_issuance", "label": "Payment to entitlement issuance", "passed": True},
    {"id": "refund_revocation", "label": "Refund / revocation lifecycle", "passed": True},
    {"id": "production_schema", "label": "Production schema installation proof", "passed": False},
)


def status() -> dict[str, object]:
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
        "ci_green": False,
        "runtime_image_green": False,
        "governed_checks_green": False,
        "live_payment_claimed": False,
        "production_green": False,
        "next_blocker": (
            "Apply and read back the reviewed Library ebook schemas on production; "
            "keep live paid checkout and end-to-end ownership unclaimed until a real "
            "provider transaction proves the full payment-to-reader chain."
        ),
        "human_authority_final": True,
    }
