from __future__ import annotations


def test_infrastructure_dashboard_shows_first_party_intelligence_and_signal_legend(client):
    response = client.get("/mission/infrastructure")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "OAP Live Signal Legend" in page
    assert "Infrastructure Intelligence" in page
    assert "First-party build gates" in page
    assert "OAP owns the system, intelligence, signal language and health model" in page
    assert "🟣" in page
    assert "Learning" in page
    assert "🟡" in page
    assert "Warning" in page
    assert "Operational controls unavailable" in page
    assert 'method="post"' not in page.lower()
