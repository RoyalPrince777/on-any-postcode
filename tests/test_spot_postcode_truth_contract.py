def test_spot_postcode_query_is_display_only_and_does_not_create_a_form(client):
    response = client.get("/the-spot?postcode=CR4%201AB")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "CR4 1AB" in page
    assert "Check local data" in page
    assert "<form" not in page
    assert "checkout, dispatch, payment" in page


def test_spot_postcode_query_is_html_escaped(client):
    page = client.get("/the-spot?postcode=%3Cscript%3Ealert(1)%3C/script%3E").get_data(as_text=True)

    assert "<script>alert(1)</script>" not in page
    assert "&lt;SCRIPT&gt;ALERT(1)&lt;/SCRIPT&gt;" in page
