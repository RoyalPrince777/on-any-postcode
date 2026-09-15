from __future__ import annotations

from mission_control import ecosystem_handoff


def test_ecosystem_chain_is_canonical_and_ordered():
    assert [item["id"] for item in ecosystem_handoff.CHAIN] == [
        "the_link",
        "market",
        "media",
        "distribution",
        "store",
    ]
    assert [item["route"] for item in ecosystem_handoff.CHAIN] == [
        "/the-link",
        "/the-spot/market",
        "/the-spot/tv-media",
        "/the-spot/distribution",
        "/oap-store",
    ]


def test_each_existing_surface_hands_forward_to_next(client):
    pairs = (
        ("/the-link", "/the-spot/market"),
        ("/the-spot/market", "/the-spot/tv-media"),
        ("/the-spot/tv-media", "/the-spot/distribution"),
        ("/the-spot/distribution", "/oap-store"),
    )
    for current, expected_next in pairs:
        response = client.get(current)
        page = response.get_data(as_text=True)
        assert response.status_code == 200
        assert 'data-oap-ecosystem-handoff="true"' in page
        assert f'href="{expected_next}"' in page


def test_oap_store_front_door_is_public_read_only_and_truthful(client):
    response = client.get("/oap-store")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert "OAP Store" in page
    assert "Certified OAP apps, games and tools" in page
    assert "Install remains locked" in page
    assert "Signed package and checksum proof required before install." in page
    assert "Guardian scanning and permission review required before install." in page
    assert 'method="post"' not in page.casefold()
    assert client.post("/oap-store").status_code == 405


def test_store_status_never_claims_install_or_external_execution():
    status = ecosystem_handoff.status()

    assert status["chain_length"] == 5
    assert status["store_front_door_registered"] is True
    assert status["catalogue_foundation"] is True
    assert status["install_enabled"] is False
    assert status["update_enabled"] is False
    assert status["package_publish_enabled"] is False
    assert status["payment_capture_enabled"] is False
    assert status["external_distribution_enabled"] is False
    assert status["human_authority_final"] is True
