from mission_control import map_live_pattern


def test_tfl_road_status_normalises_free_and_heavy_states():
    free = map_live_pattern._normalise_tfl_road({
        "id": "A23",
        "displayName": "A23",
        "statusSeverity": "Good",
        "statusSeverityDescription": "No exceptional delays",
        "statusAggregationStartDate": "2026-10-03T00:00:00Z",
    })
    heavy = map_live_pattern._normalise_tfl_road({
        "id": "A406",
        "displayName": "North Circular (A406)",
        "statusSeverity": "Serious",
        "statusSeverityDescription": "Serious delays",
        "statusAggregationStartDate": "2026-10-03T00:00:00Z",
    })
    assert free["road_state"] == "free"
    assert heavy["road_state"] == "heavy"
    assert free["authority_verified"] is True
