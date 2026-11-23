"""Static pressure tests for Koradaso invitation authority boundaries."""
from mission_control import koradaso_invites, koradaso_schema


def test_invite_permission_is_registered_but_not_auto_granted():
    sql = "\n".join(koradaso_schema.STATEMENTS)
    assert koradaso_invites.ISSUE_PERMISSION in sql
    assert "INSERT INTO oap_role_permissions" not in sql


def test_runtime_never_stores_raw_invite_token_in_audit_contract():
    import inspect
    source = inspect.getsource(koradaso_invites)
    assert "token_hash" in source
    assert 'metadata={"expires_at"' in source
    assert 'metadata={"token"' not in source


def test_claim_explicitly_does_not_grant_royal_status():
    import inspect
    source = inspect.getsource(koradaso_invites.claim_invite)
    assert '"royal_status_granted": False' in source
    assert "invite_already_claimed" in source
    assert "invite_expired" in source
    assert "invite_revoked" in source
    assert "active_identity_required" in source


def test_issue_permission_is_checked_before_insert():
    import inspect
    source = inspect.getsource(koradaso_invites.issue_invite)
    assert source.index("_has_permission") < source.index("INSERT INTO koradaso_invites")


def test_invitation_ttl_is_bounded():
    assert koradaso_invites.DEFAULT_TTL_HOURS == 72
