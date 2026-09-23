"""First-party Fashion → Commerce reconciliation, without side effects."""
import pytest

from mission_control.fashion_first_party import (
    FashionDraft,
    FashionError,
    FashionVariant,
)
from mission_control.fashion_market_bridge import fashion_market_projection

OWNER = "11111111-1111-4111-8111-111111111111"
OTHER = "22222222-2222-4222-8222-222222222222"
PRODUCT = "33333333-3333-4333-8333-333333333333"


def approved_draft():
    draft = FashionDraft(
        OWNER, PRODUCT, "OAP Hoodie", "hoodie", "oap:art/original",
        True, True, (FashionVariant("OAP-HOODIE-001", "L", "Black", 3500),),
    )
    draft.submit_review(OWNER, "rights:001")
    draft.approve(OWNER, "human:001", human_approval=True)
    return draft


def commerce(*, active=True, price=3500, name="OAP Hoodie", currency="GBP"):
    return {
        "organ": "OAP Commerce Core",
        "products": [{
            "product_id": PRODUCT,
            "name": name,
            "price_minor": price,
            "currency": currency,
            "active": active,
        }],
    }


def test_owner_scoped_first_party_market_bridge():
    result = fashion_market_projection(
        actor_id=OWNER, draft=approved_draft(), commerce=commerce()
    )
    assert result["product_id"] == PRODUCT
    assert result["fashion"]["variants"][0]["sku"] == "OAP-HOODIE-001"
    for field in ("durable_fashion_storage_verified", "publication_performed",
                  "inventory_verified", "payment_performed",
                  "external_fulfilment_performed"):
        assert result[field] is False


@pytest.mark.parametrize("changes,error", [
    ({"active": False}, "market_product_inactive"),
    ({"price": 3501}, "fashion_market_price_mismatch"),
    ({"name": "Wrong name"}, "fashion_market_product_mismatch"),
    ({"currency": "USD"}, "fashion_market_price_mismatch"),
])
def test_existing_market_mismatch_fails_closed(changes, error):
    with pytest.raises(FashionError, match=error):
        fashion_market_projection(
            actor_id=OWNER, draft=approved_draft(), commerce=commerce(**changes)
        )


def test_wrong_owner_cannot_view_market_bridge():
    with pytest.raises(FashionError, match="not_product_owner"):
        fashion_market_projection(
            actor_id=OTHER, draft=approved_draft(), commerce=commerce()
        )


def test_absent_or_duplicate_market_product_fails_closed():
    for products in ([], [commerce()["products"][0]] * 2):
        with pytest.raises(FashionError, match="owned_market_product_not_found"):
            fashion_market_projection(
                actor_id=OWNER,
                draft=approved_draft(),
                commerce={"organ": "OAP Commerce Core", "products": products},
            )


def test_invalid_market_projection_fails_closed():
    with pytest.raises(FashionError, match="untrusted_commerce_projection"):
        fashion_market_projection(
            actor_id=OWNER, draft=approved_draft(),
            commerce={"organ": "unknown", "products": commerce()["products"]},
        )


def test_stopped_draft_cannot_appear_as_approved():
    draft = approved_draft()
    draft.stop(OWNER, "STOP")
    with pytest.raises(FashionError, match="product_not_approved"):
        fashion_market_projection(
            actor_id=OWNER, draft=draft, commerce=commerce()
        )
