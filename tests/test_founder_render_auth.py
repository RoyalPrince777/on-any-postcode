from __future__ import annotations

from mission_control import (
    founder_local_auth,
    founder_recovery,
    neon_auth,
    web_security,
)

AUTH_ID = "11111111-1111-4111-8111-111111111111"


def test_founder_sign_in_prefers_render_local_verifier(monkeypatch):
    monkeypatch.setenv("OAP_HUMAN_AUTHORITY_EMAIL", "founder@example.test")
    monkeypatch.setenv("OAP_HUMAN_AUTHORITY_ID", AUTH_ID)
    monkeypatch.setattr(founder_local_auth, "bound", lambda: True)
    monkeypatch.setattr(
        founder_local_auth,
        "verify",
        lambda password: password == "existing-private-password",
    )
    monkeypatch.setattr(
        founder_local_auth,
        "issue_session_cookie",
        lambda: (
            "oap_founder_session=opaque; Path=/; Secure; HttpOnly; "
            "SameSite=Lax; Max-Age=43200"
        ),
    )

    def provider_must_not_run(*_args, **_kwargs):
        raise AssertionError("Neon provider must not run for a bound Founder")

    monkeypatch.setattr(neon_auth, "_request", provider_must_not_run)

    result = neon_auth.sign_in("founder@example.test", "existing-private-password")

    assert result.status_code == 200
    assert result.payload["user"]["id"] == AUTH_ID
    assert result.set_cookie_headers[0].startswith("oap_founder_session=")


def test_founder_wrong_render_password_stays_401(monkeypatch):
    monkeypatch.setenv("OAP_HUMAN_AUTHORITY_EMAIL", "founder@example.test")
    monkeypatch.setenv("OAP_HUMAN_AUTHORITY_ID", AUTH_ID)
    monkeypatch.setattr(founder_local_auth, "bound", lambda: True)
    monkeypatch.setattr(founder_local_auth, "verify", lambda _password: False)

    result = neon_auth.sign_in("founder@example.test", "wrong-password")

    assert result.status_code == 401
    assert neon_auth.safe_error_code(result) == "INVALID_PASSWORD"


def test_render_store_outage_is_auth_unavailable_not_bad_password(monkeypatch):
    monkeypatch.setenv("OAP_HUMAN_AUTHORITY_EMAIL", "founder@example.test")
    monkeypatch.setenv("OAP_HUMAN_AUTHORITY_ID", AUTH_ID)
    monkeypatch.setattr(founder_local_auth, "bound", lambda: True)

    def unavailable(_password):
        raise founder_local_auth.FounderLocalAuthUnavailable("store_unavailable")

    monkeypatch.setattr(founder_local_auth, "verify", unavailable)

    try:
        neon_auth.sign_in("founder@example.test", "existing-private-password")
    except neon_auth.AuthUnavailable as exc:
        assert str(exc) == "founder_local_auth_unavailable"
    else:
        raise AssertionError("Render-local outage must fail as AuthUnavailable")


def test_render_local_session_is_exposed_through_neon_bridge(monkeypatch):
    local_user = {
        "id": AUTH_ID,
        "name": "OAP Founder",
        "email": "founder@example.test",
        "emailVerified": True,
    }
    monkeypatch.setattr(founder_local_auth, "session_user", lambda _cookie: local_user)

    result = neon_auth.get_session("oap_founder_session=opaque")

    assert result.status_code == 200
    assert result.payload["user"] == local_user
    assert result.payload["session"]["id"] == "render-local-founder"


def test_bind_existing_password_requires_active_founder_proof(
    anonymous_client, monkeypatch
):
    monkeypatch.setattr(founder_recovery, "configured", lambda: True)
    monkeypatch.setattr(founder_recovery, "session_active", lambda: False)
    token = "render-founder-bind-csrf-token-value-123456"
    with anonymous_client.session_transaction() as current_session:
        current_session[web_security.CSRF_SESSION_KEY] = token

    response = anonymous_client.post(
        "/auth/recover-founder",
        data={
            "action": "bind-password",
            "csrf_token": token,
            "password": "existing-private-password",
            "password_confirmation": "existing-private-password",
            "next": "/mission/ollama",
        },
    )

    assert response.status_code == 403
    assert "Founder proof expired" in response.get_data(as_text=True)


def test_explicit_migration_mode_routes_proven_founder_to_password_bind(
    anonymous_client, monkeypatch
):
    monkeypatch.setattr(founder_recovery, "configured", lambda: True)
    monkeypatch.setattr(founder_recovery, "session_active", lambda: False)
    monkeypatch.setattr(founder_recovery, "token_allowed", lambda _code: True)
    monkeypatch.setattr(founder_recovery, "begin_session", lambda: None)
    token = "render-founder-migration-csrf-token-value-987654"
    with anonymous_client.session_transaction() as current_session:
        current_session[web_security.CSRF_SESSION_KEY] = token

    response = anonymous_client.post(
        "/auth/recover-founder",
        data={
            "mode": "bind",
            "csrf_token": token,
            "recovery_code": "existing-founder-proof-value",
            "next": "/mission/ollama",
        },
    )

    assert response.status_code == 200
    page = response.get_data(as_text=True)
    assert "Keep your existing private password" in page
    assert 'name="action" value="bind-password"' in page


def test_explicit_bind_mode_repairs_already_bound_founder(
    anonymous_client, monkeypatch
):
    monkeypatch.setattr(founder_recovery, "configured", lambda: True)
    monkeypatch.setattr(founder_recovery, "session_active", lambda: False)
    monkeypatch.setattr(founder_recovery, "token_allowed", lambda _code: True)
    monkeypatch.setattr(founder_recovery, "begin_session", lambda: None)
    monkeypatch.setattr(founder_local_auth, "bound", lambda: True)
    token = "render-founder-repair-csrf-token-value-246810"
    with anonymous_client.session_transaction() as current_session:
        current_session[web_security.CSRF_SESSION_KEY] = token

    response = anonymous_client.post(
        "/auth/recover-founder",
        data={
            "mode": "bind",
            "csrf_token": token,
            "recovery_code": "existing-founder-proof-value",
            "next": "/mission/ollama",
        },
    )

    assert response.status_code == 200
    assert "Keep your existing private password" in response.get_data(as_text=True)


def test_proven_founder_can_bind_existing_password_once(
    anonymous_client, monkeypatch
):
    monkeypatch.setattr(founder_recovery, "configured", lambda: True)
    monkeypatch.setattr(founder_recovery, "session_active", lambda: True)
    monkeypatch.setattr(
        founder_local_auth,
        "bind_existing_password",
        lambda password: (
            "bound" if password == "existing-private-password" else "unexpected"
        ),
    )
    monkeypatch.setattr(founder_recovery, "clear_session", lambda: None)
    token = "render-founder-bind-csrf-token-value-654321"
    with anonymous_client.session_transaction() as current_session:
        current_session[web_security.CSRF_SESSION_KEY] = token

    response = anonymous_client.post(
        "/auth/recover-founder",
        data={
            "action": "bind-password",
            "csrf_token": token,
            "password": "existing-private-password",
            "password_confirmation": "existing-private-password",
            "next": "/mission/ollama",
        },
    )

    assert response.status_code == 302
    assert "/enter-my-world?next=/mission/ollama" in response.headers["Location"]
    assert "render_bound=1" in response.headers["Location"]
    assert response.headers["X-OAP-Founder-Lane"] == "render-local"
    assert response.headers["X-OAP-Founder-Password-State"] == "bound"


def test_proven_founder_can_rebind_existing_password(
    anonymous_client, monkeypatch
):
    monkeypatch.setattr(founder_recovery, "configured", lambda: True)
    monkeypatch.setattr(founder_recovery, "session_active", lambda: True)
    monkeypatch.setattr(
        founder_local_auth,
        "bind_existing_password",
        lambda password: (
            "rebound" if password == "existing-private-password" else "unexpected"
        ),
    )
    monkeypatch.setattr(founder_recovery, "clear_session", lambda: None)
    token = "render-founder-rebind-csrf-token-value-135790"
    with anonymous_client.session_transaction() as current_session:
        current_session[web_security.CSRF_SESSION_KEY] = token

    response = anonymous_client.post(
        "/auth/recover-founder",
        data={
            "action": "bind-password",
            "csrf_token": token,
            "password": "existing-private-password",
            "password_confirmation": "existing-private-password",
            "next": "/mission/ollama",
        },
    )

    assert response.status_code == 302
    assert "render_bound=1" in response.headers["Location"]
    assert response.headers["X-OAP-Founder-Lane"] == "render-local"
    assert response.headers["X-OAP-Founder-Password-State"] == "rebound"


class _ExistingFounderConnection:
    def __init__(self):
        self.commands = []
        self.committed = False
        self.rolled_back = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, sql, params=()):
        self.commands.append((sql, params))

        class Result:
            def fetchone(self):
                if "SELECT identity_id FROM oap_founder_local_auth" in sql:
                    return (AUTH_ID,)
                return None

        return Result()

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


def test_local_store_rebind_updates_same_identity_without_second_row(monkeypatch):
    connection = _ExistingFounderConnection()
    monkeypatch.setattr(founder_local_auth.postgres_db, "connect", lambda: connection)
    monkeypatch.setattr(founder_local_auth.authority, "configured_identity", lambda: AUTH_ID)
    monkeypatch.setattr(
        founder_local_auth.authority,
        "configured_email",
        lambda: "founder@example.test",
    )
    monkeypatch.setattr(
        founder_local_auth.authority,
        "sync_authenticated_identity",
        lambda *_args, **_kwargs: {"is_human_authority": True},
    )
    monkeypatch.setattr(founder_local_auth.secrets, "token_bytes", lambda _size: b"s" * 16)
    monkeypatch.setattr(founder_local_auth, "_derive", lambda _password, _salt: b"v" * 32)

    result = founder_local_auth.bind_existing_password("existing-private-password")

    assert result == "rebound"
    assert connection.committed is True
    assert connection.rolled_back is False
    statements = "\n".join(sql for sql, _params in connection.commands)
    assert "UPDATE oap_founder_local_auth" in statements
    assert "INSERT INTO oap_founder_local_auth" not in statements


def test_password_only_founder_sign_in_needs_no_selector_env(monkeypatch):
    monkeypatch.delenv("OAP_HUMAN_AUTHORITY_EMAIL", raising=False)
    monkeypatch.delenv("OAP_HUMAN_AUTHORITY_ID", raising=False)
    monkeypatch.setattr(founder_local_auth, "bound", lambda: True)
    monkeypatch.setattr(
        founder_local_auth,
        "resolved_identity",
        lambda: AUTH_ID,
    )
    monkeypatch.setattr(
        founder_local_auth,
        "verify",
        lambda password: password == "existing-private-password",
    )
    monkeypatch.setattr(
        founder_local_auth,
        "issue_session_cookie",
        lambda: (
            "oap_founder_session=opaque; Path=/; Secure; HttpOnly; "
            "SameSite=Lax; Max-Age=43200"
        ),
    )

    def provider_must_not_run(*_args, **_kwargs):
        raise AssertionError("Managed Auth must not run for local password-only Founder")

    monkeypatch.setattr(neon_auth, "_request", provider_must_not_run)

    result = neon_auth.sign_in_founder("existing-private-password")

    assert result.status_code == 200
    assert result.payload["user"]["id"] == AUTH_ID
    assert result.payload["user"]["email"] == ""
    assert result.set_cookie_headers[0].startswith("oap_founder_session=")


def test_founder_auth_post_uses_local_password_without_email_selector(
    anonymous_client, monkeypatch
):
    monkeypatch.delenv("OAP_HUMAN_AUTHORITY_EMAIL", raising=False)
    monkeypatch.delenv("OAP_HUMAN_AUTHORITY_ID", raising=False)
    monkeypatch.setattr(neon_auth, "local_founder_ready", lambda: True)
    monkeypatch.setattr(
        neon_auth,
        "sign_in_founder",
        lambda password: neon_auth.AuthResult(
            status_code=200,
            payload={
                "session": {"id": "render-local-founder"},
                "user": {
                    "id": AUTH_ID,
                    "name": "OAP Founder",
                    "email": "",
                    "emailVerified": False,
                },
            },
            set_cookie_headers=(
                (
                    "oap_founder_session=opaque; Path=/; Secure; HttpOnly; "
                    "SameSite=Lax; Max-Age=43200"
                ),
            ),
        )
        if password == "existing-private-password"
        else neon_auth.AuthResult(
            status_code=401,
            payload={"code": "INVALID_PASSWORD"},
        ),
    )
    monkeypatch.setattr(
        web_security.AUTH_BURST_LIMITER,
        "allow",
        lambda _key: True,
    )
    token = "selector-free-founder-csrf-token-value-123456"
    with anonymous_client.session_transaction() as current_session:
        current_session[web_security.CSRF_SESSION_KEY] = token

    response = anonymous_client.post(
        "/auth/sign-in",
        data={
            "csrf_token": token,
            "password": "existing-private-password",
            "next": "/mission/ollama",
        },
    )

    assert response.status_code == 302
    assert response.headers["Location"].endswith("/mission/ollama")
    assert any(
        header.startswith("oap_founder_session=")
        for header in response.headers.getlist("Set-Cookie")
    )


class _ResolvedAuthorityRows:
    def fetchall(self):
        return [(AUTH_ID,)]


class _ResolvedAuthorityConnection:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False

    def execute(self, _sql, _params=()):
        return _ResolvedAuthorityRows()


def test_local_founder_resolves_single_authority_from_ledger(monkeypatch):
    monkeypatch.setattr(
        founder_local_auth.authority,
        "configured_identity",
        lambda: "",
    )
    monkeypatch.setattr(
        founder_local_auth.postgres_db,
        "configured",
        lambda: True,
    )
    monkeypatch.setattr(
        founder_local_auth.postgres_db,
        "connect",
        lambda readonly=False: _ResolvedAuthorityConnection(),
    )

    assert founder_local_auth.resolved_identity() == AUTH_ID


def test_founder_session_uses_domain_separated_gateway_secret(monkeypatch):
    monkeypatch.delenv("OAP_SESSION_SECRET", raising=False)
    monkeypatch.setenv("OAP_SMI_GATEWAY_SECRET", "g" * 64)
    monkeypatch.setattr(founder_local_auth, "_identity", lambda: AUTH_ID)
    monkeypatch.setattr(
        founder_local_auth.authority,
        "configured_email",
        lambda: "",
    )

    header = founder_local_auth.issue_session_cookie(now=1000)
    user = founder_local_auth.session_user(header, now=1001)

    assert header.startswith("oap_founder_session=")
    assert user is not None
    assert user["id"] == AUTH_ID


def test_founder_session_prefers_explicit_session_secret(monkeypatch):
    monkeypatch.setenv("OAP_SESSION_SECRET", "s" * 64)
    monkeypatch.setenv("OAP_SMI_GATEWAY_SECRET", "g" * 64)

    assert founder_local_auth._session_secret() == b"s" * 64


def test_missing_all_session_keys_fails_closed_not_500(monkeypatch):
    monkeypatch.delenv("OAP_SESSION_SECRET", raising=False)
    monkeypatch.delenv("OAP_SMI_GATEWAY_SECRET", raising=False)
    monkeypatch.setattr(founder_local_auth, "bound", lambda: True)
    monkeypatch.setattr(founder_local_auth, "verify", lambda _password: True)
    monkeypatch.setattr(
        founder_local_auth,
        "resolved_identity",
        lambda: AUTH_ID,
    )

    try:
        neon_auth.sign_in_founder("existing-private-password")
    except neon_auth.AuthUnavailable as exc:
        assert str(exc) == "founder_local_auth_unavailable"
    else:
        raise AssertionError("Missing session signing key must fail closed")
