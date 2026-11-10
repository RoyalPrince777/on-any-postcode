from __future__ import annotations

from mission_control import authority, oap_data, oap_data_views


def test_oap_data_is_a_named_first_party_product():
    product = oap_data.get_product_status()

    assert product["product"] == "OAP Data"
    assert product["owner"] == "ON ANY POSTCODE"
    assert product["consumer"] == "OAP Intelligence"
    assert product["core"] == "OAP CORE"
    assert product["raw_records_exposed"] is False
    assert product["destructive_actions_enabled"] is False
    assert len(product["domains"]) == 7
    assert product["first_party"]["oap_product"] is True
    assert product["first_party"]["oap_owned_contracts"] is True
    assert product["first_party"]["external_analytics_required"] is False
    assert product["first_party"]["external_tracking_required"] is False
    assert product["first_party"]["external_realtime_data_provider_required"] is False


def test_oap_data_dashboard_uses_product_language_only(client, monkeypatch):
    monkeypatch.setattr(oap_data_views, "_require_human_authority", lambda: None)

    response = client.get("/mission/data")
    page = response.get_data(as_text=True)

    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert "OAP Data" in page
    assert "OAP Intelligence" in page
    assert "OAP Data domains" in page
    assert "First-party boundary" in page
    assert "metadata" not in page.casefold()
    assert 'method="post"' not in page.casefold()


def test_oap_data_status_is_coarse_and_contains_no_private_records(client, monkeypatch):
    monkeypatch.setattr(oap_data_views, "_require_human_authority", lambda: None)

    response = client.get("/mission/data/status")
    payload = response.get_json()
    serialized = response.get_data(as_text=True).casefold()

    assert response.status_code == 200
    assert payload["product"] == "OAP Data"
    assert payload["raw_records_exposed"] is False
    for private_key in (
        "password",
        "secret",
        "token",
        "private_key",
        "message_body",
        "email_address",
        "phone_number",
    ):
        assert private_key not in serialized


def test_oap_data_fails_closed_without_human_authority(client, monkeypatch):
    def reject():
        raise authority.HumanAuthorityRequired("level_zero_human_authority_required")

    monkeypatch.setattr(oap_data_views, "_require_human_authority", reject)

    response = client.get("/mission/data")

    assert response.status_code == 403
    assert response.get_data(as_text=True) == "Human Authority required."


def test_oap_data_status_fails_closed_when_authority_unavailable(client, monkeypatch):
    def unavailable():
        raise authority.AuthorityUnavailable("oap_data_authority_unavailable")

    monkeypatch.setattr(oap_data_views, "_require_human_authority", unavailable)
    response = client.get("/mission/data/status")

    assert response.status_code == 503
    assert response.get_json() == {"error": {"code": "oap_data_unavailable"}}
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_oap_data_status_rejects_missing_human_authority(client, monkeypatch):
    def reject():
        raise authority.HumanAuthorityRequired("level_zero_human_authority_required")

    monkeypatch.setattr(oap_data_views, "_require_human_authority", reject)
    response = client.get("/mission/data/status")

    assert response.status_code == 403
    assert response.get_json() == {"error": {"code": "human_authority_required"}}
    assert response.headers["Cache-Control"] == "no-store"


def test_oap_data_real_authority_path_rejects_non_founder(client, monkeypatch):
    from contextlib import contextmanager

    @contextmanager
    def fake_connect(*, readonly):
        assert readonly is True
        yield object()

    def reject_authority(connection, user_id):
        raise authority.HumanAuthorityRequired("level_zero_human_authority_required")

    monkeypatch.setattr(oap_data_views.postgres_db, "connect", fake_connect)
    monkeypatch.setattr(oap_data_views.authority, "require_human_authority", reject_authority)

    response = client.get("/mission/data/status")
    assert response.status_code == 403
    assert response.get_json() == {"error": {"code": "human_authority_required"}}


def test_oap_data_real_authority_path_fails_closed_on_database_error(client, monkeypatch):
    def failed_connect(*, readonly):
        raise ConnectionError("private database details must not escape")

    monkeypatch.setattr(oap_data_views.postgres_db, "connect", failed_connect)
    response = client.get("/mission/data/status")

    assert response.status_code == 503
    assert response.get_json() == {"error": {"code": "oap_data_unavailable"}}
    assert "private database details" not in response.get_data(as_text=True)
    assert response.headers["Cache-Control"] == "no-store"


def test_founder_intelligence_posts_summary_uses_real_readonly_aggregate(client, monkeypatch):
    from contextlib import contextmanager

    @contextmanager
    def fake_connect(*, readonly):
        assert readonly is True
        class Connection:
            def execute(self, sql):
                assert sql == "SELECT COUNT(*) FROM posts"
                class Result:
                    def fetchone(self):
                        return (17,)
                return Result()
        yield Connection()

    monkeypatch.setattr(oap_data_views.postgres_db, "connect", fake_connect)
    monkeypatch.setattr(
        oap_data_views.authority, "require_human_authority",
        lambda connection, identity_id: {"is_human_authority": True},
    )
    response = client.get("/mission/data/intelligence/posts-summary")
    assert response.status_code == 200
    assert response.get_json()["value"] == 17
    assert response.get_json()["raw_records_exposed"] is False
    assert response.headers["Cache-Control"] == "no-store"


def test_founder_intelligence_posts_summary_fails_closed_for_nonfounder(client, monkeypatch):
    from contextlib import contextmanager

    @contextmanager
    def fake_connect(*, readonly):
        assert readonly is True
        yield object()

    monkeypatch.setattr(oap_data_views.postgres_db, "connect", fake_connect)
    def deny(connection, identity_id):
        raise authority.HumanAuthorityRequired("no_founder_access")
    monkeypatch.setattr(oap_data_views.authority, "require_human_authority", deny)
    response = client.get("/mission/data/intelligence/posts-summary")
    assert response.status_code == 403
    assert response.get_json() == {"error": {"code": "human_authority_required"}}


def test_founder_intelligence_posts_summary_database_failure_never_leaks(client, monkeypatch):
    def broken(*, readonly):
        raise RuntimeError("private database password")
    monkeypatch.setattr(oap_data_views.postgres_db, "connect", broken)
    response = client.get("/mission/data/intelligence/posts-summary")
    assert response.status_code == 503
    assert response.get_json() == {"error": {"code": "oap_data_unavailable"}}
    assert b"password" not in response.data
