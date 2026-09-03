from __future__ import annotations

import hashlib
import io
import shutil
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest

from mission_control import link_share, link_voice_routes


class _Result:
    def __init__(self, row=None, rows=None):
        self._row = row
        self._rows = rows or []

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
        link_share.linkup_safety, "blocked_between", lambda _first, _second: False
    )
    monkeypatch.setattr(
        link_share.link_relationships, "accepted_between", lambda _first, _second: True
    )


def _png() -> bytes:
    return b"\x89PNG\r\n\x1a\n" + b"oap-share" * 20


def test_share_schema_is_explicit_first_party_and_bounded():
    dry_run = link_share.init_schema(dry_run=True)
    joined = "\n".join(dry_run["statements"])

    assert dry_run["version"] == "link_share_v1"
    assert dry_run["applied"] is False
    assert "link_shares" in joined
    assert "media BYTEA NOT NULL" in joined
    assert "byte_size <= 26214400" in joined
    assert "kind IN ('photo','video','file')" in joined
    assert link_share.MAX_SHARE_BYTES == 25 * 1024 * 1024
    assert link_share.MAX_SENDER_STORAGE_BYTES == 500 * 1024 * 1024


def test_guardian_accepts_only_certified_matching_signatures():
    samples = {
        "image/jpeg": b"\xff\xd8\xff" + b"jpeg" * 20,
        "image/png": _png(),
        "image/webp": b"RIFF\x10\x00\x00\x00WEBP" + b"webp" * 20,
        "video/mp4": b"\x00\x00\x00\x18ftypisom" + b"video" * 20,
        "video/webm": b"\x1aE\xdf\xa3" + b"video" * 20,
        "application/pdf": b"%PDF-1.7\n" + b"pdf" * 20,
        "text/plain": b"Born Local. Built Global.\n",
    }
    expected_kinds = {
        "image/jpeg": "photo",
        "image/png": "photo",
        "image/webp": "photo",
        "video/mp4": "video",
        "video/webm": "video",
        "application/pdf": "file",
        "text/plain": "file",
    }
    for mime, media in samples.items():
        assert link_share._guardian_validate(media, mime) == (mime, expected_kinds[mime])

    with pytest.raises(ValueError, match="share_content_mismatch"):
        link_share._guardian_validate(b"not-a-png", "image/png")
    with pytest.raises(ValueError, match="unsupported_share_type"):
        link_share._guardian_validate(_png(), "application/octet-stream")
    with pytest.raises(ValueError, match="share_content_mismatch"):
        link_share._guardian_validate(b"safe\x00not-text", "text/plain")


def test_share_guard_rejects_before_storage(monkeypatch):
    monkeypatch.setattr(
        link_share.linkup_safety, "blocked_between", lambda _first, _second: True
    )
    monkeypatch.setattr(
        link_share.postgres_db,
        "connect",
        lambda *args, **kwargs: pytest.fail("database must not be reached for Block"),
    )
    with pytest.raises(ValueError, match="link_blocked"):
        link_share.create_share(
            uuid.uuid4(),
            uuid.uuid4(),
            media=_png(),
            mime_type="image/png",
            original_name="photo.png",
        )

    monkeypatch.setattr(
        link_share.linkup_safety, "blocked_between", lambda _first, _second: False
    )
    monkeypatch.setattr(
        link_share.link_relationships, "accepted_between", lambda _first, _second: False
    )
    with pytest.raises(ValueError, match="accepted_link_required"):
        link_share.create_share(
            uuid.uuid4(),
            uuid.uuid4(),
            media=_png(),
            mime_type="image/png",
            original_name="photo.png",
        )


def test_share_rejects_oversize_before_storage(monkeypatch):
    _allow_link(monkeypatch)
    monkeypatch.setattr(
        link_share.postgres_db,
        "connect",
        lambda *args, **kwargs: pytest.fail("database must not receive oversized Share"),
    )
    with pytest.raises(ValueError, match="share_too_large"):
        link_share.create_share(
            uuid.uuid4(),
            uuid.uuid4(),
            media=b"\x89PNG\r\n\x1a\n" + b"x" * link_share.MAX_SHARE_BYTES,
            mime_type="image/png",
            original_name="large.png",
        )


def test_create_share_enforces_quota_name_and_sha256(monkeypatch):
    _allow_link(monkeypatch)
    sender = str(uuid.uuid4())
    recipient = str(uuid.uuid4())
    share_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc)
    media = _png()

    def handler(query, params):
        if query.startswith("SELECT COALESCE(SUM(byte_size),0)"):
            return _Result(row=(0,))
        if query.startswith("INSERT INTO link_shares"):
            assert params[0] == sender
            assert params[1] == recipient
            assert params[2] == "photo"
            assert params[3] == "unsafe_name.png"
            assert params[4] == "image/png"
            assert params[5] == len(media)
            assert params[6] == hashlib.sha256(media).hexdigest()
            assert params[7] == media
            return _Result(row=(share_id, created_at))
        raise AssertionError(f"unexpected query: {query}")

    connection = _Connection(handler)
    monkeypatch.setattr(
        link_share.postgres_db, "connect", lambda *args, **kwargs: _Context(connection)
    )
    result = link_share.create_share(
        sender,
        recipient,
        media=media,
        mime_type="image/png",
        original_name="../unsafe<>name.png",
    )
    assert result["share_id"] == share_id
    assert result["sha256"] == hashlib.sha256(media).hexdigest()
    assert result["original_name"] == "unsafe_name.png"
    assert connection.committed is True

    quota_connection = _Connection(
        lambda query, _params: _Result(row=(link_share.MAX_SENDER_STORAGE_BYTES,))
        if query.startswith("SELECT COALESCE(SUM(byte_size),0)")
        else pytest.fail("insert must not happen after quota failure")
    )
    monkeypatch.setattr(
        link_share.postgres_db,
        "connect",
        lambda *args, **kwargs: _Context(quota_connection),
    )
    with pytest.raises(ValueError, match="share_storage_quota_reached"):
        link_share.create_share(
            sender,
            recipient,
            media=media,
            mime_type="image/png",
            original_name="photo.png",
        )


def test_share_list_is_exact_pair_and_never_returns_bytes(monkeypatch):
    _allow_link(monkeypatch)
    identity = str(uuid.uuid4())
    peer = str(uuid.uuid4())
    share_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc)
    connection = _Connection(
        lambda _query, _params: _Result(
            rows=[(share_id, identity, peer, "photo", "photo.png", "image/png", 99, created_at)]
        )
    )
    monkeypatch.setattr(
        link_share.postgres_db, "connect", lambda *args, **kwargs: _Context(connection)
    )
    result = link_share.list_shares(identity, peer)
    query, params = connection.calls[0]
    assert "(sender_id=%s AND recipient_id=%s)" in query
    assert params[:4] == (identity, peer, peer, identity)
    assert result[0]["direction"] == "sent"
    assert "media" not in result[0]
    assert "sha256" not in result[0]


def test_share_read_rechecks_integrity_and_delete_stays_sender_only(monkeypatch):
    _allow_link(monkeypatch)
    identity = str(uuid.uuid4())
    peer = str(uuid.uuid4())
    share_id = str(uuid.uuid4())
    media = _png()
    digest = hashlib.sha256(media).hexdigest()
    connection = _Connection(
        lambda _query, _params: _Result(
            row=(media, "image/png", digest, "photo.png", "photo")
        )
    )
    monkeypatch.setattr(
        link_share.postgres_db, "connect", lambda *args, **kwargs: _Context(connection)
    )
    assert link_share.read_share(identity, peer, share_id) == (
        media,
        "image/png",
        digest,
        "photo.png",
        "photo",
    )

    bad = _Connection(
        lambda _query, _params: _Result(
            row=(media, "image/png", "0" * 64, "photo.png", "photo")
        )
    )
    monkeypatch.setattr(
        link_share.postgres_db, "connect", lambda *args, **kwargs: _Context(bad)
    )
    with pytest.raises(link_share.LinkShareUnavailable, match="share_integrity_failed"):
        link_share.read_share(identity, peer, share_id)

    delete_connection = _Connection(lambda _query, _params: _Result(row=(share_id,)))
    monkeypatch.setattr(
        link_share.postgres_db,
        "connect",
        lambda *args, **kwargs: _Context(delete_connection),
    )
    monkeypatch.setattr(
        link_share.linkup_safety,
        "blocked_between",
        lambda *_args: pytest.fail("sender delete must remain available after Block"),
    )
    assert link_share.delete_share(identity, share_id) is True
    query, params = delete_connection.calls[0]
    assert "id=%s AND sender_id=%s" in query
    assert params == (share_id, identity)


def test_share_routes_require_auth_csrf_and_no_store(client, anonymous_client, monkeypatch):
    anonymous = anonymous_client.get("/linkup/share/status")
    assert anonymous.status_code == 401
    assert anonymous.get_json()["error"]["code"] == "authentication_required"

    monkeypatch.setattr(
        link_voice_routes.link_share,
        "status",
        lambda: {
            "ready": True,
            "first_party": True,
            "max_share_bytes": link_share.MAX_SHARE_BYTES,
            "allowed_mime_types": sorted(link_share.ALLOWED_MIME_TYPES),
        },
    )
    status = client.get("/linkup/share/status")
    assert status.status_code == 200
    assert status.get_json()["ready"] is True
    assert status.headers["Cache-Control"] == "no-store"
    assert status.headers["X-Content-Type-Options"] == "nosniff"

    upload = client.post(
        "/linkup/share",
        data={
            "recipient_id": str(uuid.uuid4()),
            "share": (io.BytesIO(_png()), "photo.png", "image/png"),
        },
        content_type="multipart/form-data",
    )
    assert upload.status_code == 403
    assert upload.get_json()["error"]["code"] == "csrf_failed"


def test_share_media_route_is_pair_scoped_with_safe_disposition(client, monkeypatch):
    peer = str(uuid.uuid4())
    share_id = str(uuid.uuid4())
    media = _png()
    digest = hashlib.sha256(media).hexdigest()
    monkeypatch.setattr(
        link_voice_routes.link_share,
        "read_share",
        lambda _identity, used_peer, used_share: (
            media,
            "image/png",
            digest,
            "photo.png",
            "photo",
        )
        if used_peer == peer and used_share == share_id
        else None,
    )
    response = client.get(f"/linkup/share/{share_id}/media?peer_id={peer}")
    assert response.status_code == 200
    assert response.data == media
    assert response.headers["Content-Type"].startswith("image/png")
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-OAP-Content-SHA256"] == digest
    assert response.headers["Content-Disposition"].startswith("inline;")


def test_share_browser_controller_is_same_origin_fail_closed_and_syntax_valid():
    voice_js = Path("static/linkup_voice.js").read_text(encoding="utf-8")
    share_js = Path("static/linkup_share.js").read_text(encoding="utf-8")
    template = Path("mission_control/templates/linkup.html").read_text(encoding="utf-8")

    assert 'script.src = "/static/linkup_share.js"' in voice_js
    assert 'document.querySelectorAll("button[data-runtime-locked]")' in share_js
    assert 'apiJson("/linkup/share/status")' in share_js
    assert 'picker.type = "file"' in share_js
    assert 'credentials: "same-origin"' in share_js
    assert "https://" not in share_js
    assert "http://" not in share_js
    assert "application/octet-stream" not in share_js
    assert "Private media runtime required" in template
    assert "disabled data-runtime-locked" in template

    node = shutil.which("node")
    if node:
        subprocess.run([node, "--check", "static/linkup_share.js"], check=True)
        subprocess.run([node, "--check", "static/linkup_voice.js"], check=True)
