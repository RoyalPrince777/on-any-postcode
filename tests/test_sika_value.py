from mission_control import sika_value


def test_sika_status_keeps_money_powers_locked():
    status = sika_value.status()

    assert status["ready"] is True
    assert status["real_money_movement"] is False
    assert status["cash_out_allowed"] is False
    assert status["customer_deposits_allowed"] is False
    assert status["payment_initiation_allowed"] is False
    assert status["bank_provider_required"] is True
    assert status["human_authority_final"] is True
    assert status["a4_money_movement_allowed"] is False

    lock_ids = {item["id"] for item in status["status_lights"]}
    expected = {
        "cash_out",
        "bank_account",
        "emoney",
        "crypto",
        "a4_money",
        "human_authority",
    }
    assert expected.issubset(lock_ids)


def test_my_card_is_oap_identity_not_legal_or_bank_id():
    card = sika_value.my_card("Augustine", "@earthisourturf777", founder=True)

    assert card["component"] == "My Card"
    assert card["membership_tier"] == "Founder"
    assert "not government ID" in card["privacy_note"]
    assert "bank ID" in card["privacy_note"]
    assert "payment card" in card["privacy_note"]
    assert any(badge["id"] == "founder" for badge in card["badges"])


def test_revenue_streams_are_monetisation_not_ad_dependency():
    status = sika_value.status()
    streams = {stream["id"]: stream for stream in status["revenue_streams"]}

    assert "memberships" in streams
    assert "creator_profiles" in streams
    assert "business_listings" in streams
    assert "booking" in streams
    assert streams["booking"]["state"] == "needs_finish_pack"


def test_wallet_ui_is_bank_style_without_bank_powers():
    wallet = sika_value.wallet()
    blocked = set(wallet["rules"]["blocked"])
    card_ids = {card["id"] for card in wallet["cards"]}

    assert wallet["component"] == "SIKA Wallet UI"
    assert "Monzo" in wallet["style_reference"]
    assert "sika_balance" in card_ids
    assert "membership_pot" in card_ids
    assert "bank_link" in card_ids
    assert "customer deposits" in blocked
    assert "cash-out" in blocked
    assert "payment initiation" in blocked
    assert "stored monetary value" in blocked
    assert "interest or yield" in blocked
