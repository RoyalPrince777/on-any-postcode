from __future__ import annotations

import hashlib
import io
import uuid
from datetime import datetime, timezone

import pytest

from mission_control import link_voice, link_voice_routes


class _Result:
    def __init__(self, row=None, rows=None, rowcount=0):
        self._row = row
        self._rows = rows or []
        self.rowcount = rowcount

    def fetchone(self):
        return self._row

    def fetchall(self):
        return self._rows


class _Connection:
    def __init__(self, handler):
        self.handler = handler
        self.calls = []
        self.committed = False

    def execute(self, query, params=None):
        normalized = " ".join(str(query).split())
        self.calls.append((normalized, params))
        return self.handler(normalized, params)

    def commit(self):
        self.committed = True


class _Context:
    def __init__(self, connection):
        self.connection = connection

    def __enter__(self):
        return self.connection

    def __exit__(self, exc_type, exc, tb):
        return False


def _allow_link(monkeypatch):
    monkeypatch.setattr(
        link_voice.linkup_safety, "blocked_between", lambda _first, _second: False
    )
    monkeypatch.setattr(
        link_voice.link_relationships, "accepted_between", lambda _first, _second: True
    )


def _webm() -> bytes:
    return b"\x1aE\xdf\xa3" + b"voice" * 20


def test_voice_schema_is_explicit_first_party_and_bounded():
    dry_run = link_voice.init_schema(dry_run=True)
    joined = "\n".join(dry_run["statements"])

    assert dry_run["version"] == "link_voice_v1"
    assert dry_run["applied"] is False
    assert "link_voice_notes" in joined
    assert "media BYTEA NOT NULL" in joined
    assert "byte_size <= 5242880" in joined
    assert "duration_ms <= 120000" in joined
    assert link_voice.MAX_VOICE_BYTES == 5 * 1024 * 1024
    assert link_voice.MAX_VOICE_DURATION_MS == 120_000
    assert link_voice.MAX_SENDER_STORAGE_BYTES == 100 * 1024 * 1024


def test_guardian_accepts_only_matching_audio_magic():
    samples = {
        "audio/webm": _webm(),
        "audio/ogg": b"OggS" + b"voice" * 20,
        "audio/mp4": b"\x00\x00\x00\x18ftypM4A " + b"voice" * 20,
        "audio/mpeg": b"ID3" + b"voice" * 20,
    }
    for mime, media in samples.items():
        assert link_voice._guardian_validate(media, mime) == mime

    with pytest.raises(ValueError, match="voice_content_mismatch"):
        link_voice._guardian_validate(b"not-audio", "audio/webm")
    with pytest.raises(ValueError, match="unsupported_voice_type"):
        link_voice._guardian_validate(_webm(), "application/octet-stream")


def test_guardian_rejects_oversize_before_storage(monkeypatch):
    _allow_link(monkeypatch)
    monkeypatch.setattr(
        link_voice.postgres_db,
        "connect",
        lambda *args, **kwargs: pytest.fail("database must not receive oversized Voice"),
    )

    with pytest.raises(ValueError, match="voice_too_large"):
        link_voice.create_voice(
            uuid.uuid4(),
            uuid.uuid4(),
            media=b"\x1aE\xdf\xa3" + b"x" * link_voice.MAX_VOICE_BYTES,
            mime_type="audio/webm",
        )


def test_voice_block_guard_runs_before_storage(monkeypatch):
    monkeypatch.setattr(
        link_voice.linkup_safety, "blocked_between", lambda _first, _second: True
    )
    monkeypatch.setattr(
        link_voice.postgres_db,
        "connect",
        lambda *args, **kwargs: pytest.fail("database must not be reached for Block"),
    )

    with pytest.raises(ValueError, match="link_blocked"):
        link_voice.create_voice(
            uuid.uuid4(), uuid.uuid4(), media=_webm(), mime_type="audio/webm"
        )


def test_voice_requires_accepted_link_before_storage(monkeypatch):
    monkeypatch.setattr(
        link_voice.linkup_safety, "blocked_between", lambda _first, _second: False
    )
    monkeypatch.setattr(
        link_voice.link_relationships, "accepted_between", lambda _first, _second: False
    )
    monkeypatch.setattr(
        link_voice.postgres_db,
        "connect",
        lambda *args, **kwargs: pytest.fail("database must not be reached without Link"),
    )

    with pytest.raises(ValueError, match="accepted_link_required"):
        link_voice.create_voice(
            uuid.uuid4(), uuid.uuid4(), media=_webm(), mime_type="audio/webm"
        )


def test_create_voice_enforces_quota_and_sha256(monkeypatch):
    _allow_link(monkeypatch)
    sender = str(uuid.uuid4())
    recipient = str(uuid.uuid4())
    voice_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc)
    media = _webm()

    def handler(query, params):
        if query.startswith("SELECT COALESCE(SUM(byte_size),0)"):
            return _Result(row=(0,))
        if query.startswith("INSERT INTO link_voice_notes"):
            assert params[0] == sender
            assert params[1] == recipient
            assert params[2] == "audio/webm"
            assert params[3] == len(media)
            assert params[5] == hashlib.sha256(media).hexdigest()
            assert params[6] == media
            return _Result(row=(voice_id, created_at))
        raise AssertionError(f"unexpected query: {query}")

    connection = _Connection(handler)
    monkeypatch.setattr(
        link_voice.postgres_db, "connect", lambda *args, **kwargs: _Context(connection)
    )

    result = link_voice.create_voice(
        sender, recipient, media=media, mime_type="audio/webm", duration_ms=1000
    )
    assert result["voice_id"] == voice_id
    assert result["sha256"] == hashlib.sha256(media).hexdigest()
    assert connection.committed is True

    quota_connection = _Connection(
        lambda query, _params: _Result(row=(link_voice.MAX_SENDER_STORAGE_BYTES,))
        if query.startswith("SELECT COALESCE(SUM(byte_size),0)")
        else pytest.fail("insert must not happen after quota failure")
    )
    monkeypatch.setattr(
        link_voice.postgres_db,
        "connect",
        lambda *args, **kwargs: _Context(quota_connection),
    )
    with pytest.raises(ValueError, match="voice_storage_quota_reached"):
        link_voice.create_voice(sender, recipient, media=media, mime_type="audio/webm")


def test_voice_list_is_exact_pair_and_never_returns_bytes(monkeypatch):
    _allow_link(monkeypatch)
    identity = str(uuid.uuid4())
    peer = str(uuid.uuid4())
    voice_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc)
    connection = _Connection(
        lambda _query, _params: _Result(
            rows=[(voice_id, identity, peer, "audio/webm", 99, 800, created_at)]
        )
    )
    monkeypatch.setattr(
        link_voice.postgres_db, "connect", lambda *args, **kwargs: _Context(connection)
    )

    result = link_voice.list_voice(identity, peer)
    query, params = connection.calls[0]
    assert "(sender_id=%s AND recipient_id=%s)" in query
    assert params[:4] == (identity, peer, peer, identity)
    assert result[0]["direction"] == "sent"
    assert "media" not in result[0]
    assert "sha256" not in result[0]


def test_voice_read_rechecks_integrity(monkeypatch):
    _allow_link(monkeypatch)
    identity = str(uuid.uuid4())
    peer = str(uuid.uuid4())
    note = str(uuid.uuid4())
    media = _webm()
    digest = hashlib.sha256(media).hexdigest()
    connection = _Connection(lambda _query, _params: _Result(row=(media, "audio/webm", digest)))
    monkeypatch.setattr(
        link_voice.postgres_db, "connect", lambda *args, **kwargs: _Context(connection)
    )

    assert link_voice.read_voice(identity, peer, note) == (media, "audio/webm", digest)

    bad = _Connection(lambda _query, _params: _Result(row=(media, "audio/webm", "0" * 64)))
    monkeypatch.setattr(
        link_voice.postgres_db, "connect", lambda *args, **kwargs: _Context(bad)
    )
    with pytest.raises(link_voice.LinkVoiceUnavailable, match="voice_integrity_failed"):
        link_voice.read_voice(identity, peer, note)


def test_voice_delete_is_sender_only_without_link_guard(monkeypatch):
    sender = str(uuid.uuid4())
    voice_id = str(uuid.uuid4())
    connection = _Connection(lambda _query, _params: _Result(row=(voice_id,)))
    monkeypatch.setattr(
        link_voice.postgres_db, "connect", lambda *args, **kwargs: _Context(connection)
    )
    monkeypatch.setattr(
        link_voice.linkup_safety,
        "blocked_between",
        lambda *_args: pytest.fail("sender delete must remain available after Block"),
    )

    assert link_voice.delete_voice(sender, voice_id) is True
    query, params = connection.calls[0]
    assert "id=%s AND sender_id=%s" in query
    assert params == (voice_id, sender)


def test_voice_status_route_rejects_anonymous_access(anonymous_client):
    response = anonymous_client.get("/linkup/voice/status")
    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "authentication_required"


def test_voice_status_route_is_coarse_and_no_store(client, monkeypatch):
    monkeypatch.setattr(
        link_voice_routes.link_voice,
        "status",
        lambda: {
            "ready": True,
            "first_party": True,
            "max_voice_bytes": link_voice.MAX_VOICE_BYTES,
            "max_voice_duration_ms": link_voice.MAX_VOICE_DURATION_MS,
        },
    )
    response = client.get("/linkup/voice/status")
    assert response.status_code == 200
    assert response.get_json()["ready"] is True
    assert response.get_json()["first_party"] is True
    assert response.headers["Cache-Control"] == "no-store"


def test_voice_upload_requires_csrf(client):
    response = client.post(
        "/linkup/voice",
        data={
            "recipient_id": str(uuid.uuid4()),
            "duration_ms": "1000",
            "voice": (io.BytesIO(_webm()), "voice.webm", "audio/webm"),
        },
        content_type="multipart/form-data",
    )
    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "csrf_failed"


def test_voice_media_route_is_pair_scoped_and_no_store(client, monkeypatch):
    peer = str(uuid.uuid4())
    voice_id = str(uuid.uuid4())
    media = _webm()
    digest = hashlib.sha256(media).hexdigest()
    monkeypatch.setattr(
        link_voice_routes.link_voice,
        "read_voice",
        lambda _identity, used_peer, used_voice: (media, "audio/webm", digest)
        if used_peer == peer and used_voice == voice_id
        else None,
    )

    response = client.get(f"/linkup/voice/{voice_id}/media?peer_id={peer}")
    assert response.status_code == 200
    assert response.data == media
    assert response.headers["Content-Type"].startswith("audio/webm")
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["X-OAP-Content-SHA256"] == digest
