"""Checkpoint integrity test uses small byte fixtures, never fake inference."""
import hashlib

from mission_control.studio_triposr_preflight import (
    _inspect_checkpoint,
    checkpoint_preflight,
)


def test_unconfigured_preflight_fails_closed(monkeypatch):
    monkeypatch.delenv("OAP_STUDIO_TRIPOSR_MODEL_DIR", raising=False)
    result = checkpoint_preflight()
    assert result["status"] == "blocked"
    assert result["execution_granted"] is False
    assert result["checkpoint_loaded"] is False


def test_bounded_checkpoint_hash_match_and_rejection(tmp_path):
    raw = b"test fixture only"
    digest = hashlib.sha256(raw).hexdigest()
    model = tmp_path / "model.ckpt"
    model.write_bytes(raw)
    assert _inspect_checkpoint(tmp_path, size=len(raw), expected_sha256=digest)["status"] == "matched"
    model.write_bytes(b"x" * len(raw))
    assert _inspect_checkpoint(tmp_path, size=len(raw), expected_sha256=digest)["status"] == "failed"
    model.unlink()
    assert _inspect_checkpoint(tmp_path, size=len(raw), expected_sha256=digest)["status"] == "blocked"


def test_acquisition_rejects_nonprivate_directory(tmp_path, monkeypatch):
    from mission_control.studio_triposr_preflight import acquire_checkpoint

    tmp_path.chmod(0o755)
    monkeypatch.setenv("OAP_STUDIO_TRIPOSR_MODEL_DIR", str(tmp_path))
    assert acquire_checkpoint()["reason"] == "private_model_directory_required"


def test_acquisition_does_not_replace_existing_checkpoint(tmp_path, monkeypatch):
    from mission_control.studio_triposr_preflight import acquire_checkpoint

    tmp_path.chmod(0o700)
    monkeypatch.setenv("OAP_STUDIO_TRIPOSR_MODEL_DIR", str(tmp_path))
    model = tmp_path / "model.ckpt"
    model.write_bytes(b"existing")
    assert acquire_checkpoint()["reason"] == "existing_checkpoint_not_replaced"
    assert model.read_bytes() == b"existing"
