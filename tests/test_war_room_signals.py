from __future__ import annotations


def test_war_room_renders_first_party_signal_legend_without_purple_proof_state(client):
    response = client.get("/mission/war-room")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "OAP Live Signal Legend" in page
    assert "First-party rule: OAP owns the War Room" in page
    assert "🟣" in page
    assert "Learning" in page
    assert "🟡" in page
    assert "Warning" in page
    assert "🔴" in page
    assert "Critical" in page
    assert "🟢" in page
    assert "Healthy" in page
    assert "proof-verified is shown as 🔵" in page
    assert "mc-war-rubric--purple" not in page
    assert "mc-war-rating--purple" not in page
