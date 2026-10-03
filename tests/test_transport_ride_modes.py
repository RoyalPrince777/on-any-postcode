from __future__ import annotations

from mission_control import global_transport_views


def test_transport_menu_is_collapsed_to_seven_doors():
    assert [name for name, _ in global_transport_views.PUBLIC_DOORS] == [
        "Journey",
        "Move",
        "Ride",
        "Logistics",
        "Guardian",
        "Operators",
        "Control Center",
    ]


def test_ride_contains_car_and_ebike_modes():
    modes = {item["id"]: item for item in global_transport_views.RIDE_MODES}

    assert set(modes) == {"car", "ebike"}
    assert modes["car"]["experience"] == "ride_hailing"
    assert modes["car"]["request_route"] == "/transport/ride/request"
    assert modes["car"]["external_dispatch_performed"] is False

    assert modes["ebike"]["experience"] == "shared_hire"
    assert modes["ebike"]["availability_route"] == "/transport/shared-bikes/mitcham"
    assert modes["ebike"]["operator_gateway"] == "OAP Operator Gateway"
    assert modes["ebike"]["external_unlock_performed"] is False
    assert modes["ebike"]["external_payment_performed"] is False
