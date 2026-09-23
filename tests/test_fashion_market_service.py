"""Service-level first-party Fashion bridge uses trusted Commerce dashboard."""
import pytest

from mission_control import product_core_services
from mission_control.fashion_first_party import (
    FashionDraft,
    FashionError,
    FashionVariant,
)

OWNER = "11111111-1111-4111-8111-111111111111"
OTHER = "22222222-2222-4222-8222-222222222222"
PRODUCT = "33333333-3333-4333-8333-333333333333"


def test_owner_fashion_market_projection_uses_first_party_read_path(monkeypatch):
    draft = FashionDraft(
        OWNER, PRODUCT, "OAP Hoodie", "hoodie", "oap:art/original",
        True, True, (FashionVariant("OAP-HOODIE-001", "XL", "Black", 3500),),
    )
    draft.submit_review(OWNER, "rights:001")
    draft.approve(OWNER, "human:001", human_approval=True)
    calls = []

    def verified_commerce(identity):
        calls.append(identity)
        return {
            "organ": "OAP Commerce Core",
            "products": [{
                "product_id": PRODUCT, "name": "OAP Hoodie",
                "price_minor": 3500, "currency": "GBP", "active": True,
            }],
        }

    monkeypatch.setattr(
        product_core_services, "commerce_dashboard", verified_commerce
    )
    result = product_core_services.owner_fashion_market_projection(OWNER, draft)
    assert calls == [OWNER]
    assert result["durable_fashion_storage_verified"] is False
    assert result["publication_performed"] is False
    with pytest.raises(FashionError, match="not_product_owner"):
        product_core_services.owner_fashion_market_projection(OTHER, draft)
