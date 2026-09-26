from mission_control import routing, routing_federation


def test_national_shard_stays_locked_without_owned_graph_proof(monkeypatch):
    monkeypatch.setattr(
        routing,
        "status",
        lambda: {"uk_wide_owned_graph_proven": False},
    )
    start = {"latitude": 53.4808, "longitude": -2.2426}
    end = {"latitude": 52.4862, "longitude": -1.8904}
    assert routing_federation.select_shard(start, end) is None


def test_national_shard_unlocks_only_after_owned_graph_proof(monkeypatch):
    monkeypatch.setattr(
        routing,
        "status",
        lambda: {"uk_wide_owned_graph_proven": True},
    )
    monkeypatch.setenv("OAP_OSRM_BASE_URL", "https://routing.example.test")
    start = {"latitude": 53.4808, "longitude": -2.2426}
    end = {"latitude": 52.4862, "longitude": -1.8904}

    shard = routing_federation.select_shard(start, end)

    assert shard is not None
    assert shard.shard_id == "united_kingdom_owned_graph"
    assert shard.label == "United Kingdom"


def test_uk_owned_graph_probe_requires_all_four_nations(monkeypatch):
    calls = []

    def fake_map_route(**kwargs):
        calls.append(kwargs)
        return {
            "geometry": {"type": "LineString", "coordinates": [[0, 0], [1, 1]]},
            "distance_m": 1000,
        }

    monkeypatch.setattr(routing, "map_route", fake_map_route)
    monkeypatch.setattr(routing, "provider_ownership", lambda: "oap_owned")

    state = routing._probe_owned_uk_graph()

    assert state["proven"] is True
    assert set(state["routes_proven"]) == {
        "england",
        "scotland",
        "wales",
        "northern_ireland",
    }
    assert len(calls) == 4
