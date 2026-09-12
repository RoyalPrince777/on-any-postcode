from mission_control.products import SPOT_CAPABILITIES


def test_runner_is_not_a_second_public_product_capability():
    ids = {item["id"] for item in SPOT_CAPABILITIES}
    assert "infrastructure" in ids
    assert "runner" not in ids
