"""One disposable POSIX image worker; stdin/stdout pipes only, no Flask import.

This resource boundary is not an OS security sandbox. Parent supplies no service
credentials; CPU/address-space/core/file limits are set before media imports.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

MAX_WALL_SECONDS = 7
MAX_CPU_SECONDS = 5
MAX_MEMORY_BYTES = 512 * 1024 * 1024
MAX_RESULT_BYTES = 128 * 1024


def apply_limits() -> None:
    """Fail closed when POSIX resource enforcement is unavailable."""
    import resource

    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))
    resource.setrlimit(resource.RLIMIT_CPU, (MAX_CPU_SECONDS, MAX_CPU_SECONDS))
    resource.setrlimit(resource.RLIMIT_AS, (MAX_MEMORY_BYTES, MAX_MEMORY_BYTES))


def main() -> None:
    try:
        apply_limits()
        sys.dont_write_bytecode = True
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
        from mission_control.studio_face_detection import MAX_IMAGE_BYTES, detect_faces

        # Bound pipe input as well as the HTTP request; don't consume excess.
        raw = sys.stdin.buffer.read(4 * MAX_IMAGE_BYTES // 3 + 1025)
        if len(raw) > 4 * MAX_IMAGE_BYTES // 3 + 1024:
            raise ValueError("face_image_too_large")
        payload = json.loads(raw)
        result = detect_faces(payload.get("image_data"))
        envelope = {"result": result}
    except (TypeError, ValueError) as exc:
        allowed = {"face_image_too_large", "face_image_dimensions_exceeded"}
        envelope = {"error": str(exc) if str(exc) in allowed else "invalid_face_image"}
    except Exception:  # noqa: BLE001 - never export decoder internals or media.
        envelope = {"error": "face_detector_unavailable"}
    encoded = json.dumps(envelope, separators=(",", ":")).encode("utf-8")
    if len(encoded) > MAX_RESULT_BYTES:
        encoded = b'{"error":"face_detector_unavailable"}'
    sys.stdout.buffer.write(encoded)


if __name__ == "__main__":
    main()
