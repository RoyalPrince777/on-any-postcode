from mission_control import routing


def test_endpoint_near_requested_accepts_local_geometry():
    geometry = {
        "type": "LineString",
        "coordinates": [
            [-3.1791, 51.4816],
            [-3.9436, 51.6214],
        ],
    }
    assert routing._endpoint_near_requested(
        geometry,
        start_lat=51.4816,
        start_lon=-3.1791,
        end_lat=51.6214,
        end_lon=-3.9436,
    )


def test_endpoint_near_requested_rejects_distant_snap():
    geometry = {
        "type": "LineString",
        "coordinates": [
            [-0.1687, 51.4036],
            [-0.0877, 51.5079],
        ],
    }
    assert routing._endpoint_near_requested(
        geometry,
        start_lat=51.4816,
        start_lon=-3.1791,
        end_lat=51.6214,
        end_lon=-3.9436,
    ) is False
