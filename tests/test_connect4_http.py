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
