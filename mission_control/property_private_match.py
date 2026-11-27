"""Private pre-market eligibility matching; no delivery, payments or public routes."""
from collections.abc import Callable
from decimal import Decimal
from typing import Any

from oap.contracts import BrainRequest, Recommendation
from oap.smi.smi_core import SMICore

from . import property_advertising as ads

Gate = Callable[[dict[str, Any], dict[str, Any]], bool]


def eligible_match(
    record: dict[str, Any],
    buyer: dict[str, Any],
    *,
    seller_permission: Gate,
    buyer_qualification: Gate,
    authority_check: ads.AuthorityCheck | None = None,
    certified_check: ads.CertifiedCheck | None = None,
    reviewer_check: ads.ReviewerCheck | None = None,
) -> bool:
    """Return eligibility only, never a listing or personal data.

    Inputs must come from authenticated server-side stores. The two mandatory
    gates must verify current scoped seller permission for private introductions
    and buyer identity, consent and financial qualification respectively.
    Advertising authority alone does not authorize a private introduction.
    This function does not issue grants or authorize actual delivery.
    """
    try:
        if record.get("state") != "APPROVED" or not record.get("authority_evidence_ref"):
            return False
        ads._require_live_reviewer(record, reviewer_check)
        ads._verified(
            record, record["authority_evidence_ref"],
            authority_check=authority_check, certified_check=certified_check,
        )
        if seller_permission(record, buyer) is not True:
            return False
        if buyer_qualification(record, buyer) is not True:
            return False
        country = ads._required(buyer.get("country"), "country", 120)
        currency = ads._required(buyer.get("currency"), "currency", 3).upper()
        category = ads._required(buyer.get("category"), "category", 32).lower()
        locality = ads._required(buyer.get("locality"), "locality", 160)
        if (
            country.casefold() != record["country"].casefold()
            or currency != record["currency"]
            or category != record["category"]
            or locality.casefold() != record["locality"].casefold()
        ):
            return False
        postcode = buyer.get("postcode")
        if postcode is not None:
            district = ads._required(postcode, "postcode", 32).upper()
            actual = ads._required(record.get("postcode"), "postcode", 32).upper()
            if district != actual and district != actual.split()[0]:
                return False
        price = Decimal(ads._money(record["price"]))
        budget = Decimal(ads._money(buyer.get("max_price")))
        return price > 0 and budget >= price
    except Exception:  # noqa: BLE001 - malformed data or unavailable gate denies.
        return False


def review_match(
    brain: SMICore,
    record: dict[str, Any],
    buyer: dict[str, Any],
    *,
    request_id: str,
    identity_id: str,
    seller_permission: Gate,
    buyer_qualification: Gate,
    authority_check: ads.AuthorityCheck | None = None,
    certified_check: ads.CertifiedCheck | None = None,
    reviewer_check: ads.ReviewerCheck | None = None,
) -> Recommendation:
    """Submit a minimal private review to the existing brain and its HRM.

    Only authenticated server-side callers may supply the brain, identity,
    records and gates. This is not a delivery or approval endpoint.
    Recheck live permission before any later consequential action.
    """
    eligible = eligible_match(
        record, buyer, seller_permission=seller_permission,
        buyer_qualification=buyer_qualification,
        authority_check=authority_check, certified_check=certified_check,
        reviewer_check=reviewer_check,
    )
    return brain.process(BrainRequest(
        request_id=request_id,
        identity_id=identity_id,
        task_type="PROPERTY",
        high_impact=True,
        content=(
            "Private property eligibility review. "
            + ("Eligibility checks passed; human review required."
               if eligible else "Eligibility blocked; do not introduce parties.")
        ),
        oapcore={"property_match_eligible": eligible, "delivery_allowed": False},
    ))
