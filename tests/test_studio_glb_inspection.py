"""GLB read-only inspection: structural checks, not a runtime rendering proof."""
import hashlib
import json
import struct

import pytest

from mission_control.studio_local_media import inspect_owned_glb


def glb(doc, binary=None):
    body = json.dumps(doc).encode()
    body += b" " * (-len(body) % 4)
    chunks = struct.pack("<I4s", len(body), b"JSON") + body
    if binary is not None:
        chunks += struct.pack("<I4s", len(binary), b"BIN\x00") + binary
    return struct.pack("<4sII", b"glTF", 2, 12 + len(chunks)) + chunks


@pytest.fixture
def owner(tmp_path, monkeypatch):
    monkeypatch.setenv("OAP_STUDIO_PRIVATE_ASSET_ROOT", str(tmp_path))
    directory = tmp_path / "owner"
    directory.mkdir()
    return directory


def test_inspection_hash_and_no_runtime_claim(owner):
    data = glb({"asset": {"version": "2.0"}, "buffers": [{"byteLength": 4}],
                "meshes": []}, b"abcd")
    (owner / "asset.glb").write_bytes(data)
    result = inspect_owned_glb(owner_directory=str(owner), asset_name="asset.glb")
    assert result["sha256"] == hashlib.sha256(data).hexdigest()
    assert result["container_inspected"] is True
    assert result["runtime_verified"] is False
    assert result["full_schema_validated"] is False
    assert result["render_verified"] is False


@pytest.mark.parametrize("data", [
    b"bad",
    glb({"asset": {"version": "1.0"}}),
    glb({"asset": {"version": "2.0"}, "images": [{"uri": "https://example.invalid/a"}]}),
    glb({"asset": {"version": "2.0"}, "extensions": {"X": {"uri": "../a"}}}),
    glb({"asset": {"version": "2.0"}, "buffers": [{"byteLength": 5}]}, b"abcd"),
    glb({"asset": {"version": "2.0"}}) + b"extra",
])
def test_invalid_or_external_asset_rejected(owner, data):
    (owner / "asset.glb").write_bytes(data)
    with pytest.raises(ValueError):
        inspect_owned_glb(owner_directory=str(owner), asset_name="asset.glb")


def test_owner_boundary(owner, tmp_path):
    (tmp_path / "outside.glb").write_bytes(glb({"asset": {"version": "2.0"}}))
    (owner / "linked.glb").symlink_to(tmp_path / "outside.glb")
    with pytest.raises(OSError):
        inspect_owned_glb(owner_directory=str(owner), asset_name="linked.glb")
    with pytest.raises(ValueError):
        inspect_owned_glb(owner_directory=str(owner), asset_name="../outside.glb")
    with pytest.raises(ValueError):
        inspect_owned_glb(owner_directory=str(tmp_path), asset_name="outside.glb")
