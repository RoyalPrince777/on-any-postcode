from __future__ import annotations

import pytest

from oap.cloud_drive_private import PrivateDrive, principal_from_verified_session
from oap.cloud_private_store import CloudAccessError, PrivateObjectStore


def _verified(owner):
    return principal_from_verified_session(
        {"session": {"id": "server-session"}, "user": {"id": owner}}
    )


@pytest.mark.parametrize(
    "payload",
    [None, {}, {"user": {"id": "alice"}}, {"session": {"id": "x"}},
     {"session": {"id": ""}, "user": {"id": "alice"}},
     {"session": {"id": "x"}, "user": {"id": ""}}],
)
def test_invalid_auth_session_denied(payload):
    with pytest.raises(CloudAccessError):
        principal_from_verified_session(payload)


def test_private_drive_cross_owner_denied(tmp_path):
    drive = PrivateDrive(PrivateObjectStore(tmp_path))
    alice = _verified("alice")
    bob = _verified("bob")
    object_id = drive.put(alice, b"alice secret")
    assert drive.get(alice, object_id) == b"alice secret"
    with pytest.raises(CloudAccessError):
        drive.get(bob, object_id)


def test_client_string_cannot_be_principal(tmp_path):
    drive = PrivateDrive(PrivateObjectStore(tmp_path))
    with pytest.raises(CloudAccessError):
        drive.put("alice", b"forbidden")


def test_no_publication_interface(tmp_path):
    drive = PrivateDrive(PrivateObjectStore(tmp_path))
    assert not hasattr(drive, "publish")
    assert not hasattr(drive, "public_get")
