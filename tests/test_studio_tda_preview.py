import hashlib
import json

import pytest

from mission_control import studio_tda_preview as tda


def stage(tmp_path):
    root = tmp_path / "tda-preview"
    root.mkdir(mode=0o700)
    data = {"index.html": b"<script>function load(s,url){s.src=url;}</script>",
            "game.js": b"window.game=1;", "babylon.js": b"window.BABYLON={};"}
    for name, value in data.items():
        (root / name).write_bytes(value)
    (root / "manifest.json").write_text(json.dumps({
        name: hashlib.sha256(value).hexdigest() for name, value in data.items()
    }))
    return root


def test_exact_candidate_and_no_publication(tmp_path):
    stage(tmp_path)
    version, data = tda.candidate(str(tmp_path))
    assert "TDA_ASSETS" in tda.document(data)
    assert "s.src=url;" not in tda.document(data)
    result = tda.publication_preflight(str(tmp_path), version)
    assert result["status"] == "blocked"
    assert result["published"] is False
    assert result["execution_granted"] is False


def test_reject_stale_digest(tmp_path):
    stage(tmp_path)
    with pytest.raises(ValueError, match="candidate_version_changed"):
        tda.publication_preflight(str(tmp_path), "stale")


def test_reject_tamper_and_symlink(tmp_path):
    root = stage(tmp_path)
    (root / "game.js").write_bytes(b"changed")
    with pytest.raises(ValueError, match="candidate_hash_mismatch"):
        tda.candidate(str(tmp_path))
    (root / "game.js").unlink()
    (root / "game.js").symlink_to(root / "babylon.js")
    with pytest.raises(OSError):
        tda.candidate(str(tmp_path))
