from contextlib import contextmanager
from pathlib import Path

from mission_control import public_store

ROOT = Path(__file__).resolve().parents[1]


def test_signal_roundtrip_probe_is_residue_free_and_uses_signal_scope():
    text = (ROOT / "mission_control" / "public_store.py").read_text()

    assert "oap-signal-probe-" in text
    assert "PUBLIC_SIGNAL_SCOPE" in text
    assert "connection.rollback()" in text
    assert "decoded == expected" in text
    assert "EXISTS(SELECT 1 FROM users WHERE id=%s)" in text
    assert "EXISTS(SELECT 1 FROM posts WHERE id=%s)" in text


def test_signal_payload_decoder_matches_public_feed_shape():
    raw = '{"name":"OAP Probe","body":"useful local signal"}'

    assert public_store._decode_object(raw) == {
        "name": "OAP Probe",
        "body": "useful local signal",
    }


def test_render_durability_requires_signal_roundtrip(monkeypatch):
    user_columns = {
        "id",
        "username",
        "display_name",
        "postcode",
        "borough",
        "county",
        "country",
        "continent",
        "status",
        "updated_at",
    }
    post_columns = {
        "id",
        "user_id",
        "body",
        "scope",
        "postcode",
        "status",
        "created_at",
    }
    rows = [("users", column) for column in user_columns]
    rows.extend(("posts", column) for column in post_columns)

    class SchemaResult:
        @staticmethod
        def fetchall():
            return rows

    class SchemaConnection:
        @staticmethod
        def execute(_sql):
            return SchemaResult()

    @contextmanager
    def fake_connect(*, readonly=False):
        assert readonly is True
        yield SchemaConnection()

    monkeypatch.setenv("RENDER", "true")
    monkeypatch.setattr(public_store.postgres_db, "configured", lambda: True)
    monkeypatch.setattr(public_store.postgres_db, "connect", fake_connect)

    public_store._clear_runtime_caches()
    monkeypatch.setattr(public_store, "_signal_roundtrip_probe", lambda: False)
    not_proven = public_store.status()
    assert not_proven["schema_ready"] is True
    assert not_proven["signal_roundtrip_ready"] is False
    assert not_proven["durable"] is False

    public_store._clear_runtime_caches()
    monkeypatch.setattr(public_store, "_signal_roundtrip_probe", lambda: True)
    proven = public_store.status()
    assert proven["schema_ready"] is True
    assert proven["signal_roundtrip_ready"] is True
    assert proven["durable"] is True
    public_store._clear_runtime_caches()
