def test_route_empire_browser_and_http_flow(client, csrf):
    page = client.get("/arena/route-empire")
    assert page.status_code == 200
    body = page.get_data(as_text=True)
    assert "Route Empire" in body
    assert "synthetic local board" in body
    assert "route_empire.js" in body

    assert client.post("/arena/route-empire/start", json={"location":"Mitcham","players":["A","B"]}).status_code == 403
    headers = {"X-OAP-CSRF": csrf["csrf_token"]}
    started = client.post(
        "/arena/route-empire/start",
        json={"location":"Mitcham","players":["Alpha","Bravo"]},
        headers=headers,
    )
    assert started.status_code == 201
    state = started.get_json()
    assert state["status"] == "active"
    assert state["location_label"] == "Mitcham"
    assert state["payments"] is False
    assert state["precise_location_used"] is False

    claimed = client.post(
        "/arena/route-empire/action",
        json={"action":"claim","node_id":"north","request_id":"httpclaim0001"},
        headers=headers,
    )
    assert claimed.status_code == 200
    assert next(n for n in claimed.get_json()["nodes"] if n["id"] == "north")["owner_id"]

    ended = client.post(
        "/arena/route-empire/action",
        json={"action":"end_turn","request_id":"httpturn00001"},
        headers=headers,
    )
    assert ended.status_code == 200
    assert ended.get_json()["current_player_name"] == "Bravo"
