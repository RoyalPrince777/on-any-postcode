import pytest

from mission_control import music_purchases


def test_music_price_floors_and_pay_more():
    expected = {"single": 100, "ep": 300, "album": 500, "deluxe": 700}
    for edition, floor in expected.items():
        quote = music_purchases.price_intent(edition)
        assert quote["minimum_amount_minor"] == floor
        assert quote["amount_minor"] == floor
        assert quote["pay_more_allowed"] is True
        assert quote["payment_capture_performed"] is False
        assert quote["sika_execution_performed"] is False
        assert quote["ownership_created"] is False

        more = music_purchases.price_intent(edition, floor + 250)
        assert more["amount_minor"] == floor + 250


def test_music_price_rejects_below_floor():
    with pytest.raises(ValueError, match="minimum_album_price_is_500_minor"):
        music_purchases.price_intent("album", 499)


def test_purchase_schema_requires_settlement_before_owned_item():
    schema = "\n".join(music_purchases.SCHEMA_STATEMENTS)
    assert music_purchases.MUSIC_PURCHASE_MIGRATION_VERSION == "0017_oap_music_purchases"
    assert "PAYMENT_REQUIRED" in schema
    assert "SETTLED" in schema
    assert "oap_music_owned_items" in schema
    assert "purchase_id UUID NOT NULL UNIQUE" in schema
    assert "UNIQUE(buyer_identity_id,item_type,item_id)" in schema
