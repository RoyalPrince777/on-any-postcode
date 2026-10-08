"""Private KORADASO Library route and visibility contracts."""


def test_private_koradaso_route_requires_sign_in(anonymous_client):
    response = anonymous_client.get(
        "/library/my-library/koradaso-heritage", follow_redirects=False
    )
    assert response.status_code in (302, 303, 401, 403)
    assert "Collection storage is not enabled yet" not in response.get_data(
        as_text=True
    )


def test_private_koradaso_entry_is_only_on_signed_in_library(client, monkeypatch):
    from mission_control import web_security

    monkeypatch.setattr(web_security, "private_authority_allowed", lambda user: True)
    page = client.get("/library/my-library")
    assert page.status_code == 200
    assert 'href="/library/my-library/koradaso-heritage"' in page.get_data(
        as_text=True
    )

    private = client.get("/library/my-library/koradaso-heritage")
    body = private.get_data(as_text=True)
    assert private.status_code == 200
    assert "KORADASO Heritage" in body
    assert "Collection storage is not enabled yet" in body
    assert "Uploads, sharing and publication remain disabled" in body
    assert private.headers["Cache-Control"] == "no-store"
    assert private.headers["X-Frame-Options"] == "DENY"


def test_koradaso_collection_is_not_publicly_listed(anonymous_client):
    public = anonymous_client.get("/library")
    assert public.status_code == 200
    assert "KORADASO Heritage" not in public.get_data(as_text=True)


def test_non_founder_cannot_open_or_discover_private_collection(client, monkeypatch):
    from mission_control import web_security

    monkeypatch.setattr(web_security, "private_authority_allowed", lambda user: False)
    page = client.get("/library/my-library")
    assert page.status_code == 200
    assert 'href="/library/my-library/koradaso-heritage"' not in page.get_data(
        as_text=True
    )
    denied = client.get("/library/my-library/koradaso-heritage")
    assert denied.status_code == 403
    assert "KORADASO Heritage" not in denied.get_data(as_text=True)
