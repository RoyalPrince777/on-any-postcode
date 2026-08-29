from __future__ import annotations

from contextlib import contextmanager
from datetime import UTC, datetime

from mission_control import public_store


class FakeResult:
    def __init__(self, rows=()):
        self.rows = list(rows)

    def fetchall(self):
        return self.rows

    def fetchone(self):
        return self.rows[0] if self.rows else None


class SnapshotConnection:
    def execute(self, sql, parameters=None):
        del parameters
        if "scope=%s AND status='published'" in sql and "SELECT body FROM" in sql:
            return FakeResult((('{"name":"Neo","body":"Signal"}',),))
        if "SELECT postcode,body" in sql:
            return FakeResult(
                (("Ghana Team Room", '{"name":"Visitor","message":"Hello"}'),)
            )
        if "SELECT body,COUNT(*)" in sql:
            return FakeResult((("Ghana", 2),))
        if "SELECT display_name,country" in sql:
            return FakeResult((("Visitor", "Ghana"),))
        raise AssertionError(sql)


def test_snapshot_projects_only_bounded_public_fields(monkeypatch):
    @contextmanager
    def fake_connect(*, readonly=False):
        assert readonly is True
        yield SnapshotConnection()

    monkeypatch.setattr(public_store.postgres_db, "connect", fake_connect)

    result = public_store.snapshot()

    assert result == {
        "signal_posts": [{"name": "Neo", "body": "Signal"}],
        "team_messages": [
            {"room": "Ghana Team Room", "name": "Visitor", "message": "Hello"}
        ],
        "flag_counts": {"Ghana": 2},
        "durable": True,
    }


def test_private_profile_query_is_restricted_to_verified_owner(monkeypatch):
    identity_id = "11111111-1111-4111-8111-111111111111"

    class ProfileConnection:
        def execute(self, sql, parameters=None):
            assert "WHERE id=%s AND status='active'" in sql
            assert parameters == (identity_id,)
            return FakeResult(
                (("Private Neo", "SW1A 1AA", "Westminster", "London", "UK", "Europe"),)
            )

    @contextmanager
    def fake_connect(*, readonly=False):
        assert readonly is True
        yield ProfileConnection()

    monkeypatch.setattr(public_store.postgres_db, "connect", fake_connect)

    assert public_store.get_profile(identity_id) == {
        "nickname": "Private Neo",
        "postcode": "SW1A 1AA",
        "borough": "Westminster",
        "county": "London",
        "country": "UK",
        "continent": "Europe",
    }


def test_founder_sync_uses_selector_for_authority_but_does_not_store_email(
    monkeypatch,
):
    identity_id = "11111111-1111-4111-8111-111111111111"
    statements = []
    authority_sync = {}

    class SyncConnection:
        def execute(self, sql, parameters=None):
            statements.append((sql, parameters))
            return FakeResult()

        @staticmethod
        def commit():
            return None

    @contextmanager
    def fake_connect(*, readonly=False):
        assert readonly is False
        yield SyncConnection()

    def fake_authority_sync(connection, **values):
        assert isinstance(connection, SyncConnection)
        authority_sync.update(values)

    monkeypatch.setattr(public_store.postgres_db, "connect", fake_connect)
    monkeypatch.setattr(
        public_store.authority,
        "sync_authenticated_identity",
        fake_authority_sync,
    )

    public_store.ensure_authenticated_user(
        identity_id,
        email="founder@example.test",
        display_name="Founder",
        email_verified=True,
        store_email=False,
    )

    user_parameters = statements[0][1]
    assert user_parameters[0] == identity_id
    assert str(user_parameters[1]).startswith("oap-session-")
    assert user_parameters[2:] == (None, "Founder")
    assert authority_sync["email"] == "founder@example.test"
    assert authority_sync["email_verified"] is True


def test_list_conversations_serializes_only_owned_projection(monkeypatch):
    updated_at = datetime(2026, 8, 24, 12, 0, tzinfo=UTC)

    class ConversationConnection:
        def execute(self, sql, parameters=None):
            assert "WHERE c.identity_id=%s" in sql
            assert parameters == ("11111111-1111-4111-8111-111111111111",)
            return FakeResult(
                (("22222222-2222-4222-8222-222222222222", "OAP", updated_at, 4, "Hi"),)
            )

    @contextmanager
    def fake_connect(*, readonly=False):
        assert readonly is True
        yield ConversationConnection()

    from mission_control import smi_chat_runtime

    monkeypatch.setattr(smi_chat_runtime.postgres_db, "connect", fake_connect)

    result = smi_chat_runtime.list_conversations(
        "11111111-1111-4111-8111-111111111111"
    )

    assert result[0]["conversation_id"] == "22222222-2222-4222-8222-222222222222"
    assert result[0]["updated_at"] == "2026-08-24T12:00:00+00:00"
    assert result[0]["message_count"] == 4
