"""OAP Store catalogue UI is searchable without changing release permissions."""


def test_store_has_accessible_search_and_release_filter(client):
    response = client.get("/store")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert 'id="store-search"' in html
    assert 'id="store-filter"' in html
    assert 'aria-live="polite"' in html
    assert 'value="install"' in html
    assert 'value="open"' in html
    assert 'value="planned"' in html
    assert 'card.hidden = !matches' in html
    assert 'id="store-empty" hidden' in html


def test_finance_ui_cannot_offer_unproven_downloads(client):
    html = client.get("/store").get_data(as_text=True)
    for app_id, name in (("oap.pay", "OAP Pay"), ("oap.bank", "OAP Bank")):
        section = html.split(f'data-oap-store-app="{app_id}"', 1)[1].split("</section>", 1)[0]
        assert 'data-release="open"' in section
        assert "INSTALL NOT YET PROVEN" in section
        assert f"Install {name}" not in section
