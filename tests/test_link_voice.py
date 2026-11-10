from __future__ import annotations

import hashlib
import io
import uuid
from datetime import UTC, datetime

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
    monkeypatch.setattr(
        link_voice.link_youth_safety,
        "require_contact_allowed",
        lambda _first, _second: {"allowed": True},
    )


def _webm() -> bytes:
    return b"\x1aE\xdf\xa3" + b"voice" * 20


def test_voice_schema_is_explicit_first_party_and_bounded():
    dry_run = link_voice.init_schema(dry_run=True)
    joined = "\n".join(dry_run["statements"])

    assert dry_run["version"] == "link_voice_v2"
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
    created_at = datetime.now(UTC)
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
            assert params[7] == "voice"
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
    created_at = datetime.now(UTC)
    connection = _Connection(
        lambda _query, _params: _Result(
            rows=[(voice_id, identity, peer, "audio/webm", 99, 800, created_at, "voice")]
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


def test_ptt_kind_is_validated_and_persisted(monkeypatch):
    _allow_link(monkeypatch)
    sender = str(uuid.uuid4())
    recipient = str(uuid.uuid4())
    voice_id = str(uuid.uuid4())
    created_at = datetime.now(UTC)
    media = _webm()

    def handler(query, params):
        if query.startswith("SELECT COALESCE(SUM(byte_size),0)"):
            return _Result(row=(0,))
        if query.startswith("INSERT INTO link_voice_notes"):
            assert params[7] == "ptt"
            return _Result(row=(voice_id, created_at))
        raise AssertionError(f"unexpected query: {query}")

    connection = _Connection(handler)
    monkeypatch.setattr(
        link_voice.postgres_db, "connect", lambda *args, **kwargs: _Context(connection)
    )

    result = link_voice.create_voice(
        sender,
        recipient,
        media=media,
        mime_type="audio/webm",
        duration_ms=900,
        kind="ptt",
    )

    assert result["kind"] == "ptt"


def test_ptt_kind_rejects_unknown_mode_before_storage(monkeypatch):
    _allow_link(monkeypatch)
    monkeypatch.setattr(
        link_voice.postgres_db,
        "connect",
        lambda *args, **kwargs: pytest.fail("database must not receive invalid PTT kind"),
    )

    with pytest.raises(ValueError, match="invalid_voice_kind"):
        link_voice.create_voice(
            uuid.uuid4(),
            uuid.uuid4(),
            media=_webm(),
            mime_type="audio/webm",
            kind="radio-copy",
        )


def test_standalone_ptt_status_is_public_but_linkup_ptt_stays_protected(anonymous_client):
    public_status = anonymous_client.get("/ptt/status")
    assert public_status.status_code == 200
    payload = public_status.get_json()
    assert payload["first_party"] is True
    assert payload["paired"] is False
    assert payload["ready"] is False

    protected_status = anonymous_client.get("/linkup/ptt/status")
    assert protected_status.status_code == 401
    assert protected_status.get_json()["error"]["code"] == "authentication_required"

    protected_post = anonymous_client.post("/linkup/ptt")
    assert protected_post.status_code == 401


def test_guest_ptt_status_reports_active_temporary_pair(anonymous_client, monkeypatch):
    identity = str(uuid.uuid4())
    peer = str(uuid.uuid4())
    with anonymous_client.session_transaction() as current_session:
        current_session["oap_ptt_guest_id"] = identity

    monkeypatch.setattr(
        link_voice_routes.link_voice,
        "status",
        lambda: {
            "ptt_ready": True,
            "first_party": True,
            "max_voice_bytes": 1024,
            "max_voice_duration_ms": 5000,
        },
    )
    monkeypatch.setattr(
        link_voice_routes.ptt_guest,
        "active_pair",
        lambda who: {"active": True, "peer_id": peer, "relationship_id": str(uuid.uuid4())},
    )

    response = anonymous_client.get("/ptt/status")
    assert response.status_code == 200
    payload = response.get_json()
    assert payload["ready"] is True
    assert payload["paired"] is True
    assert payload["peer_id"] == peer
    assert payload["transport"] == "oap_voice_store"


def test_guest_ptt_history_and_media_use_current_pair(anonymous_client, monkeypatch):
    identity = str(uuid.uuid4())
    peer = str(uuid.uuid4())
    voice_id = str(uuid.uuid4())
    with anonymous_client.session_transaction() as current_session:
        current_session["oap_ptt_guest_id"] = identity

    monkeypatch.setattr(
        link_voice_routes.ptt_guest,
        "active_pair",
        lambda who: {"active": True, "peer_id": peer, "relationship_id": str(uuid.uuid4())},
    )
    monkeypatch.setattr(
        link_voice_routes.link_voice,
        "list_voice",
        lambda who, other: [
            {
                "voice_id": voice_id,
                "direction": "received",
                "mime_type": "audio/webm",
                "byte_size": 8,
                "duration_ms": 500,
                "created_at": "2026-10-23T10:00:00+00:00",
                "kind": "ptt",
            },
            {
                "voice_id": str(uuid.uuid4()),
                "direction": "received",
                "mime_type": "audio/webm",
                "byte_size": 8,
                "duration_ms": 500,
                "created_at": "2026-10-23T09:59:00+00:00",
                "kind": "voice",
            },
        ],
    )
    media = b"\x1aE\xdf\xa3test"
    digest = hashlib.sha256(media).hexdigest()
    monkeypatch.setattr(
        link_voice_routes.link_voice,
        "read_voice",
        lambda who, other, note: (media, "audio/webm", digest) if note == voice_id else None,
    )

    history = anonymous_client.get("/ptt/voice")
    assert history.status_code == 200
    voices = history.get_json()["voices"]
    assert len(voices) == 1
    assert voices[0]["voice_id"] == voice_id
    assert voices[0]["kind"] == "ptt"

    response = anonymous_client.get(f"/ptt/voice/{voice_id}/media")
    assert response.status_code == 200
    assert response.data == media
    assert response.headers["Content-Type"] == "audio/webm"
    assert response.headers["X-OAP-Content-SHA256"] == digest


def test_room_ptt_fans_out_only_to_current_members(anonymous_client, monkeypatch):
    identity = str(uuid.uuid4())
    peer_a = str(uuid.uuid4())
    peer_b = str(uuid.uuid4())
    owner = str(uuid.uuid4())
    with anonymous_client.session_transaction() as current_session:
        current_session["oap_ptt_room_identity_id"] = identity
        current_session["oap_ptt_room_owner_id"] = owner
        current_session[link_voice_routes.web_security.CSRF_SESSION_KEY] = (
            "ptt-room-csrf-token-value-1234567890"
        )

    monkeypatch.setattr(
        link_voice_routes.ptt_guest,
        "room_state",
        lambda who, room_owner: {
            "active": True,
            "identity_id": who,
            "owner_id": room_owner,
            "member_ids": [identity, peer_a, peer_b],
            "member_count": 3,
        },
    )
    monkeypatch.setattr(
        link_voice_routes.link_voice,
        "status",
        lambda: {"ptt_ready": True},
    )
    observed = []

    def create_voice(sender, recipient, **kwargs):
        observed.append((sender, recipient, kwargs))
        return {
            "voice_id": str(uuid.uuid4()),
            "kind": "ptt",
            "byte_size": len(kwargs["media"]),
        }

    monkeypatch.setattr(link_voice_routes.link_voice, "create_voice", create_voice)

    response = anonymous_client.post(
        "/ptt/room",
        data={
            "duration_ms": "500",
            "voice": (io.BytesIO(_webm()), "room.webm", "audio/webm"),
        },
        headers={"X-OAP-CSRF": "ptt-room-csrf-token-value-1234567890"},
        content_type="multipart/form-data",
    )

    assert response.status_code == 201
    assert response.get_json()["delivered"] == 2
    assert {recipient for _sender, recipient, _kwargs in observed} == {peer_a, peer_b}
    assert all(sender == identity for sender, _recipient, _kwargs in observed)
    assert all(kwargs["kind"] == "ptt" for _sender, _recipient, kwargs in observed)


def test_room_ptt_history_merges_received_and_dedupes_sent_per_peer(anonymous_client, monkeypatch):
    identity = str(uuid.uuid4())
    peer_a = str(uuid.uuid4())
    peer_b = str(uuid.uuid4())
    owner = str(uuid.uuid4())
    with anonymous_client.session_transaction() as current_session:
        current_session["oap_ptt_room_identity_id"] = identity
        current_session["oap_ptt_room_owner_id"] = owner

    monkeypatch.setattr(
        link_voice_routes.ptt_guest,
        "room_state",
        lambda who, room_owner: {
            "active": True,
            "identity_id": who,
            "owner_id": room_owner,
            "member_ids": [identity, peer_a, peer_b],
            "member_count": 3,
        },
    )

    sent_id = str(uuid.uuid4())
    received_a = str(uuid.uuid4())
    received_b = str(uuid.uuid4())

    def list_voice(who, peer):
        if peer == peer_a:
            return [
                {
                    "voice_id": received_a,
                    "direction": "received",
                    "kind": "ptt",
                    "created_at": "2026-10-23T11:00:00+00:00",
                },
                {
                    "voice_id": sent_id,
                    "direction": "sent",
                    "kind": "ptt",
                    "created_at": "2026-10-23T10:59:00+00:00",
                },
            ]
        return [
            {
                "voice_id": received_b,
                "direction": "received",
                "kind": "ptt",
                "created_at": "2026-10-23T11:01:00+00:00",
            },
            {
                "voice_id": str(uuid.uuid4()),
                "direction": "sent",
                "kind": "ptt",
                "created_at": "2026-10-23T10:59:00+00:00",
            },
        ]

    monkeypatch.setattr(link_voice_routes.link_voice, "list_voice", list_voice)

    response = anonymous_client.get("/ptt/room/voice")
    assert response.status_code == 200
    voices = response.get_json()["voices"]
    assert [voice["voice_id"] for voice in voices] == [received_b, received_a, sent_id]
    assert {voice["peer_id"] for voice in voices} <= {peer_a, peer_b}


def test_room_ptt_media_rejects_peer_outside_room(anonymous_client, monkeypatch):
    identity = str(uuid.uuid4())
    owner = str(uuid.uuid4())
    allowed_peer = str(uuid.uuid4())
    outsider = str(uuid.uuid4())
    with anonymous_client.session_transaction() as current_session:
        current_session["oap_ptt_room_identity_id"] = identity
        current_session["oap_ptt_room_owner_id"] = owner

    monkeypatch.setattr(
        link_voice_routes.ptt_guest,
        "room_state",
        lambda who, room_owner: {
            "active": True,
            "identity_id": who,
            "owner_id": room_owner,
            "member_ids": [identity, allowed_peer],
            "member_count": 2,
        },
    )
    monkeypatch.setattr(
        link_voice_routes.link_voice,
        "read_voice",
        lambda *args, **kwargs: pytest.fail("outsider media must not be read"),
    )

    response = anonymous_client.get(
        f"/ptt/room/voice/{uuid.uuid4()}/media?peer_id={outsider}"
    )
    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "ptt_room_peer_required"


def test_standalone_ptt_preserves_authenticated_saved_contact_mode(client, monkeypatch):
    peer = str(uuid.uuid4())
    observed = {}
    monkeypatch.setattr(
        link_voice_routes.link_voice,
        "status",
        lambda: {
            "ptt_ready": True,
            "first_party": True,
            "max_voice_bytes": link_voice.MAX_VOICE_BYTES,
            "max_voice_duration_ms": link_voice.MAX_VOICE_DURATION_MS,
        },
    )
    monkeypatch.setattr(
        link_voice_routes.link_voice,
        "create_voice",
        lambda sender, recipient, **kwargs: observed.update(
            sender=sender, recipient=recipient, kwargs=kwargs
        ) or {
            "voice_id": str(uuid.uuid4()),
            "kind": "ptt",
            "byte_size": len(kwargs["media"]),
        },
    )
    with client.session_transaction() as current_session:
        current_session[link_voice_routes.web_security.CSRF_SESSION_KEY] = (
            "saved-contact-csrf-token-value-1234567890"
        )

    status = client.get("/ptt/status")
    assert status.status_code == 200
    assert status.get_json()["ready"] is True
    assert status.get_json()["authenticated_contact_mode"] is True

    response = client.post(
        "/ptt",
        data={
            "recipient_id": peer,
            "duration_ms": "500",
            "voice": (io.BytesIO(_webm()), "ptt.webm", "audio/webm"),
        },
        headers={"X-OAP-CSRF": "saved-contact-csrf-token-value-1234567890"},
        content_type="multipart/form-data",
    )
    assert response.status_code == 201
    assert observed["sender"] == "11111111-1111-4111-8111-111111111111"
    assert observed["recipient"] == peer
    assert observed["kwargs"]["kind"] == "ptt"
