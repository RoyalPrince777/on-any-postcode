from __future__ import annotations

import pytest

from oap.cloud_private_store import MAX_BYTES, CloudAccessError, PrivateObjectStore


def test_private_roundtrip(tmp_path):
    store = PrivateObjectStore(tmp_path)
    object_id = store.put(owner_id="alice", authenticated_owner_id="alice", data=b"private")
    assert store.get(owner_id="alice", authenticated_owner_id="alice", object_id=object_id) == b"private"


def test_cross_owner_denied(tmp_path):
    store = PrivateObjectStore(tmp_path)
    object_id = store.put(owner_id="alice", authenticated_owner_id="alice", data=b"private")
    with pytest.raises(CloudAccessError):
        store.get(owner_id="alice", authenticated_owner_id="bob", object_id=object_id)
    with pytest.raises(CloudAccessError):
        store.put(owner_id="alice", authenticated_owner_id="bob", data=b"forbidden")


def test_path_traversal_rejected(tmp_path):
    store = PrivateObjectStore(tmp_path)
    with pytest.raises(ValueError):
        store.get(owner_id="alice", authenticated_owner_id="alice", object_id="../../secrets")


def test_size_limit(tmp_path):
    store = PrivateObjectStore(tmp_path)
    with pytest.raises(ValueError):
        store.put(owner_id="alice", authenticated_owner_id="alice", data=b"x" * (MAX_BYTES + 1))


def test_symlink_is_denied(tmp_path):
    store = PrivateObjectStore(tmp_path)
    path = tmp_path / "personal"
    owner_key = __import__("hashlib").sha256(b"alice").hexdigest()
    directory = path / owner_key
    directory.mkdir(parents=True)
    object_id = "a" * 32
    (directory / object_id).symlink_to(tmp_path / "target")
    with pytest.raises(CloudAccessError):
        store.get(owner_id="alice", authenticated_owner_id="alice", object_id=object_id)
