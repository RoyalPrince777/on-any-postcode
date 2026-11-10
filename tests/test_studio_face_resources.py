"""Real disposable-process tests; no human images, camera or production host."""
import base64
import json
import os
import subprocess
import sys
from io import BytesIO
from pathlib import Path

import pytest
from PIL import Image

from mission_control import studio_face_detection as vision

ROOT = Path(__file__).resolve().parents[1]


def _image(format):
    out = BytesIO()
    Image.new("RGB", (160, 120), (80, 120, 170)).save(out, format=format)
    mime = "jpeg" if format == "JPEG" else format.lower()
    return f"data:image/{mime};base64," + base64.b64encode(out.getvalue()).decode()


@pytest.mark.parametrize("format", ["PNG", "JPEG", "WEBP"])
def test_genuine_isolated_decoder_accepts_supported_stills(format):
    result = vision.detect_faces_bounded(_image(format))
    assert result["face_count"] == 0
    assert result["identity_verified"] is False
    assert result["raw_content_retained"] is False


def test_isolated_decoder_rejects_invalid_media_without_echo():
    with pytest.raises(ValueError, match="^invalid_face_image$"):
        vision.detect_faces_bounded("data:image/png;base64,ZmFrZQ==")


def test_timeout_kills_and_reaps_child_before_next_frame(tmp_path, monkeypatch):
    pidfile = tmp_path / "worker.pid"
    worker = tmp_path / "stall.py"
    worker.write_text(
        "import os,time\n"
        f"open({str(pidfile)!r}, 'w').write(str(os.getpid()))\n"
        "time.sleep(60)\n"
    )
    original = vision._WORKER_PATH
    monkeypatch.setattr(vision, "_WORKER_PATH", worker)
    monkeypatch.setattr(vision, "MAX_WALL_SECONDS", 0.5)
    with pytest.raises(RuntimeError, match="^face_detector_timeout$"):
        vision.detect_faces_bounded(_image("PNG"))
    pid = int(pidfile.read_text())
    with pytest.raises(ProcessLookupError):
        os.kill(pid, 0)
    monkeypatch.setattr(vision, "_WORKER_PATH", original)
    monkeypatch.setattr(vision, "MAX_WALL_SECONDS", 7)
    assert vision.detect_faces_bounded(_image("PNG"))["face_count"] == 0


def test_actual_resource_limits_deny_excess_allocation():
    code = f"""
import json, resource, sys
sys.path.insert(0, {str(ROOT)!r})
from mission_control.studio_face_worker import apply_limits, MAX_MEMORY_BYTES
apply_limits()
denied = False
try:
    bytearray(MAX_MEMORY_BYTES * 2)
except MemoryError:
    denied = True
print(json.dumps({{'denied': denied, 'memory': resource.getrlimit(resource.RLIMIT_AS),
                  'cpu': resource.getrlimit(resource.RLIMIT_CPU),
                  'core': resource.getrlimit(resource.RLIMIT_CORE),
                  'files': resource.getrlimit(resource.RLIMIT_FSIZE)}}))
"""
    result = subprocess.run(
        [sys.executable, "-I", "-c", code], capture_output=True, timeout=7, check=True,
    )
    proof = json.loads(result.stdout)
    assert proof == {"denied": True, "memory": [512 * 1024 * 1024] * 2,
                     "cpu": [5, 5], "core": [0, 0], "files": [0, 0]}


def test_worker_does_not_inherit_service_credentials(tmp_path, monkeypatch):
    worker = tmp_path / "environment.py"
    worker.write_text(
        "import os,sys\n"
        "assert 'OAP_PRIMARY_DATABASE_URL' not in os.environ\n"
        "assert 'OAP_SESSION_SECRET' not in os.environ\n"
        "sys.stdout.write('{\"result\":{\"identity_verified\":false}}')\n"
    )
    monkeypatch.setenv("OAP_PRIMARY_DATABASE_URL", "must-not-be-inherited")
    monkeypatch.setenv("OAP_SESSION_SECRET", "must-not-be-inherited")
    monkeypatch.setattr(vision, "_WORKER_PATH", worker)
    assert vision.detect_faces_bounded(_image("PNG"))["identity_verified"] is False
