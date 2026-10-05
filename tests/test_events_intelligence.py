from mission_control import events_intelligence


def test_ram_meter_uses_exactly_seven_truthful_stages():
    cases = [
        (0, "Quiet For Now 👀"),
        (15, "Warming Up"),
        (35, "Getting Ram 🔥"),
        (55, "Ram"),
        (75, "Proper Ram"),
        (90, "About To Be Ram Out 🚨"),
        (100, "RAM OUT 🔥"),
    ]
    for confirmed, label in cases:
        result = events_intelligence.ram_meter(confirmed, 100)
        assert result["stage"] == label
        assert result["percent"] == confirmed
        assert result["spaces_left"] == 100 - confirmed


def test_ram_meter_never_counts_watchers_or_fake_capacity():
    result = events_intelligence.ram_meter(84, 100)
    assert result == {
        "confirmed": 84,
        "capacity": 100,
        "spaces_left": 16,
        "percent": 84,
        "stage": "Proper Ram",
    }


def test_momentum_has_exactly_five_stages():
    labels = [events_intelligence.momentum_stage(i) for i in range(5)]
    assert labels == [
        "Cold",
        "Moving",
        "Heating Up 🔥",
        "Flying 🔥🔥",
        "Going Mad 🔥🔥🔥",
    ]
