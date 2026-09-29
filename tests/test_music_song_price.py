import pytest

from mission_control import music_entitlements, music_public_views


def test_song_price_minimum_is_one_pound_and_pay_more_allowed():
    one = music_entitlements.song_price_intent(100)
    assert one["currency"] == "GBP"
    assert one["minimum_amount_minor"] == 100
    assert one["amount_minor"] == 100
    assert one["pay_more_allowed"] is True
    assert one["payment_capture_performed"] is False
    assert one["sika_execution_performed"] is False

    more = music_entitlements.song_price_intent(725)
    assert more["amount_minor"] == 725


def test_song_price_rejects_below_one_pound():
    with pytest.raises(ValueError, match="minimum_song_price_is_1_gbp"):
        music_entitlements.song_price_intent(99)


def test_public_song_price_contract_is_real_route():
    from flask import Flask

    app = Flask(__name__)
    app.register_blueprint(music_public_views.bp)
    client = app.test_client()

    ok = client.get("/music/api/song-price?amount_minor=250")
    assert ok.status_code == 200
    payload = ok.get_json()
    assert payload["amount_minor"] == 250
    assert payload["minimum_amount_minor"] == 100
    assert payload["payment_capture_performed"] is False

    low = client.get("/music/api/song-price?amount_minor=50")
    assert low.status_code == 400
