from mission_control import light_signals


def test_learning_is_locked_to_purple():
    learning = next(
        item for item in light_signals.LIGHT_SIGNALS if item["id"] == "learning"
    )

    assert learning == {
        "id": "learning",
        "emoji": "🟣",
        "label": "Learning / Processing",
        "colour": "purple",
    }
    assert light_signals.validate_light_signals()["passed"] is True


def test_light_signals_are_unique_and_text_labelled():
    signals = light_signals.get_public_light_signals()

    assert signals["validation"]["checks"]["signals"] == 8
    assert all(item["emoji"] and item["label"] for item in signals["lights"])
    assert "not a duplicate OAP Signal system" in signals["boundary"]


def test_spot_does_not_publish_internal_status_legend(client):
    page = client.get("/the-spot").get_data(as_text=True)

    assert "OAP Light Signals" not in page
    assert "Learning / Processing" not in page
    assert "Visual status language only" not in page
