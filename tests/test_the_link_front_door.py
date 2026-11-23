from __future__ import annotations


def test_the_link_front_door_is_complete_and_public_safe(anonymous_client):
    response = anonymous_client.get("/the-link")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    for label in (
        "People",
        "Link Up",
        "🌍 Earth",
        "National Anthem",
        "Pulse",
        "Signal",
        "Opportunities",
        "On Any Postcode Maps",
        "OAP Direct",
        "Movement",
        "Travel",
        "Private by design",
    ):
        assert label in page
    assert "Your accepted Links and Certified connections." in page
    assert "Public Empire links" in page
    assert '<summary>More</summary>' in page
    assert '<section class="mc-panel" aria-label="Connect">' in page
    assert '<h2 id="link-views-title">' not in page
    assert page.count('<summary>More</summary>') == 1
    assert page.count('href="/travel/direct"') == 1
    assert page.count('href="/the-spot/distribution"') == 1
    assert "Community Power" not in page
    assert "World Rooms" not in page
    assert "verified people" not in page.casefold()
    assert 'href="/linkup?intent=message"' in page
    assert 'href="/linkup"' not in page
    assert page.count('<summary>More</summary>') == 1
    # The People action must reach protected connections, not bounce between
    # the two anonymous landing pages without a working directory.
    assert "next=/linkup" in page or "next=%2Flinkup" in page
    assert 'href="/my-card"' in page
    assert 'href="/the-spot/postcode-rooms"' in page
    assert 'href="/pulse"' in page
    assert 'href="/the-spot/signal"' in page
    assert 'href="/the-spot/discovery"' in page
    assert 'href="/oap-map"' in page
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


def test_the_link_mobile_cards_are_aligned_and_routes_preserved():
    from pathlib import Path

    page = Path("mission_control/templates/the_link.html").read_text(encoding="utf-8")
    assert "@media (max-width:640px)" in page
    assert "grid-template-columns:repeat(2,minmax(0,1fr))" in page
    assert "min-height:56px" in page
    assert "overflow-wrap:anywhere" in page
    assert "clip:rect(0,0,0,0)" in page  # secondary descriptions accessible but visually quiet
    assert "href=\"/oap-map\"" in page
    assert "linkup_front_door" in page
