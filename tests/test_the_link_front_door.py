from __future__ import annotations


def test_the_link_front_door_is_complete_and_public_safe(anonymous_client):
    response = anonymous_client.get("/the-link")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    for label in (
        "People",
        "Link Up",
        "Empire Power",
        "Pulse",
        "Signal",
        "Opportunities",
        "Maps",
        "OAP Direct",
        "Movement",
        "Travel",
        "Private by design",
    ):
        assert label in page
    assert "Find Certified people and local connections." in page
    assert "Public Empire links" in page
    assert "Community Power" not in page
    assert "verified people" not in page.casefold()
    assert 'href="/linkup"' in page
    assert 'href="/the-spot/postcode-rooms"' in page
    assert 'href="/pulse"' in page
    assert 'href="/the-spot/signal"' in page
    assert 'href="/the-spot/discovery"' in page
    assert 'href="/maps"' in page
    assert 'href="/travel/direct"' in page
    assert 'href="/movement"' in page
    assert 'href="/travel"' in page
    assert 'method="post"' not in page.lower()
    assert "Inbox" not in page
    assert "email" not in page.lower()
    assert "password" not in page.lower()


def test_the_link_does_not_reflect_query_input(anonymous_client):
    attack = '<script>alert("link")</script>'
    page = anonymous_client.get("/the-link", query_string={"q": attack}).get_data(as_text=True)

    assert attack not in page
    assert "&lt;script&gt;" not in page
