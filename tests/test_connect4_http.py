def test_connect4_http_flow(client, csrf):
    page=client.get("/arena/connect4")
    assert page.status_code==200
    body=page.get_data(as_text=True)
    assert "Connect 4" in body
    assert "connect4.js" in body

    headers={"X-OAP-CSRF":csrf["csrf_token"]}
    assert client.post("/arena/connect4/start",json={"player_one":"A","player_two":"B"}).status_code==403
    started=client.post("/arena/connect4/start",json={"player_one":"Alpha","player_two":"Bravo"},headers=headers)
    assert started.status_code==201
    assert started.get_json()["current_player_name"]=="Alpha"

    dropped=client.post("/arena/connect4/drop",json={"column":0,"request_id":"http-move-0001"},headers=headers)
    assert dropped.status_code==200
    assert dropped.get_json()["board"][5][0]==1
    assert dropped.get_json()["current_player_name"]=="Bravo"


def test_connect4_agent_move_http(client, csrf):
    headers={"X-OAP-CSRF":csrf["csrf_token"]}
    started=client.post(
        "/arena/connect4/start",
        json={"player_one":"Alpha","player_two":"Panther"},
        headers=headers,
    )
    assert started.status_code==201

    human=client.post(
        "/arena/connect4/drop",
        json={"column":0,"request_id":"human-move-0001"},
        headers=headers,
    )
    assert human.status_code==200
    assert human.get_json()["current_player_id"]=="p2"

    agent=client.post(
        "/arena/connect4/agent-move",
        json={"agent_key":"panther","difficulty":"strong","request_id":"agent-move-0001"},
        headers=headers,
    )
    assert agent.status_code==200
    body=agent.get_json()
    assert body["agent"]["key"]=="panther"
    assert body["agent"]["fit_stars"]==7
    assert body["current_player_id"]=="p1"
    assert sum(cell==2 for row in body["board"] for cell in row)==1


def test_arena_agent_catalogue_http(client):
    response=client.get("/arena/agents")
    assert response.status_code==200
    body=response.get_json()
    assert body["defaults"]["connect4"]=="panther"
    assert body["defaults"]["chess"]=="owl"
    assert body["fair_play"]["hidden_information_access"] is False
