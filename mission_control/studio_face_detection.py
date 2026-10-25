"""Founder-private still-image face boxes for canonical OAP Studio Vision.

No identity inference, liveness proof, frame storage, network calls, or implicit
camera access. The caller owns authorisation, CSRF and request-rate boundaries.
"""
from __future__ import annotations

import base64
import binascii
import json
import re
import subprocess
import sys
from io import BytesIO
from pathlib import Path
from threading import BoundedSemaphore
from typing import Any

from mission_control.studio_face_worker import MAX_RESULT_BYTES, MAX_WALL_SECONDS

MAX_IMAGE_BYTES = 3 * 1024 * 1024
MAX_IMAGE_PIXELS = 4_000_000
MAX_IMAGE_SIDE = 4096

# One costly decode/detection per process. A fast, non-blocking busy reply
# is safer than keeping multiple uploaded face images queued in worker memory.
# This is NOT a distributed/global worker limit or a CPU-time timeout.
SINGLE_FRAME_PROCESS_SLOT = BoundedSemaphore(value=1)
_DATA_URL = re.compile(r"\Adata:(image/(?:jpeg|png|webp));base64,([A-Za-z0-9+/=]+)\Z", re.IGNORECASE)
_FORMATS = {"image/jpeg": "JPEG", "image/png": "PNG", "image/webp": "WEBP"}
_WORKER_PATH = Path(__file__).with_name("studio_face_worker.py")


def detect_faces_bounded(image_data: object) -> dict[str, Any]:
    """Decode only in a disposable, memory/CPU-bounded child; reap on timeout.

    No shell, temporary image files, inherited service credentials or Flask
    context. subprocess.run kills and waits for the child before timeout exits.
    The caller keeps shared admission until this function has returned/raised.
    """
    if not isinstance(image_data, str):
        raise TypeError("invalid_face_image")
    if len(image_data) > 4 * MAX_IMAGE_BYTES // 3 + 256:
        raise ValueError("face_image_too_large")
    try:
        completed = subprocess.run(
            [sys.executable, "-I", str(_WORKER_PATH)],
            input=json.dumps({"image_data": image_data}).encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            env={"OPENBLAS_NUM_THREADS": "1", "OMP_NUM_THREADS": "1",
                 "MKL_NUM_THREADS": "1"},
            timeout=MAX_WALL_SECONDS,
            check=False,
        )
    except subprocess.TimeoutExpired:
        raise RuntimeError("face_detector_timeout") from None
    except OSError:
        raise RuntimeError("face_detector_unavailable") from None
    if completed.returncode != 0 or len(completed.stdout) > MAX_RESULT_BYTES:
        raise RuntimeError("face_detector_unavailable")
    try:
        envelope = json.loads(completed.stdout)
    except (ValueError, UnicodeError):
        raise RuntimeError("face_detector_unavailable") from None
    if not isinstance(envelope, dict):
        # A bad worker response is an unavailable service, not bad user input.
        # Preserve the route's 503 rather than its 400 type handler.
        raise RuntimeError("face_detector_unavailable")  # noqa: TRY004
    error = envelope.get("error")
    if isinstance(error, str) and error in {
        "invalid_face_image", "face_image_too_large", "face_image_dimensions_exceeded",
    }:
        raise ValueError(error)
    result = envelope.get("result")
    if error or not isinstance(result, dict) or result.get("identity_verified") is not False:
        raise RuntimeError("face_detector_unavailable")
    return result


def detect_faces(image_data: object) -> dict[str, Any]:
    """Count frontal faces in one explicitly submitted data-URL image.

    Returns only pixel coordinates and non-identifying metadata. No media or
    image hash is saved/returned. A missing local detector fails closed.
    """
    if not isinstance(image_data, str):
        raise TypeError("invalid_face_image")
    # Reject before allocating an unbounded decoded buffer.
    if len(image_data) > (4 * MAX_IMAGE_BYTES // 3 + 256):
        raise ValueError("face_image_too_large")
    match = _DATA_URL.fullmatch(image_data)
    if match is None:
        raise ValueError("invalid_face_image")
    mime = match.group(1).lower()
    try:
        raw = base64.b64decode(match.group(2), validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError("invalid_face_image") from exc
    if not raw:
        raise ValueError("invalid_face_image")
    if len(raw) > MAX_IMAGE_BYTES:
        raise ValueError("face_image_too_large")

    try:
        from PIL import Image, UnidentifiedImageError
    except ImportError as exc:
        raise RuntimeError("face_detector_unavailable") from exc
    try:
        with Image.open(BytesIO(raw)) as header:
            width, height = header.size
            actual_format = header.format
    except (OSError, ValueError, UnidentifiedImageError, Image.DecompressionBombError) as exc:
        raise ValueError("invalid_face_image") from exc
    if actual_format != _FORMATS[mime]:
        raise ValueError("face_image_format_mismatch")
    if (
        width < 1 or height < 1
        or width > MAX_IMAGE_SIDE or height > MAX_IMAGE_SIDE
        or width * height > MAX_IMAGE_PIXELS
    ):
        raise ValueError("face_image_dimensions_exceeded")

    try:
        import cv2
        import numpy as np
    except ImportError as exc:
        raise RuntimeError("face_detector_unavailable") from exc

    try:
        cv2.setNumThreads(1)
        frame = cv2.imdecode(np.frombuffer(raw, dtype=np.uint8), cv2.IMREAD_COLOR)
    except cv2.error as exc:
        raise ValueError("invalid_face_image") from exc
    if frame is None or frame.shape[1] != width or frame.shape[0] != height:
        raise ValueError("invalid_face_image")
    try:
        cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        if cascade.empty():
            raise RuntimeError("face_detector_unavailable")
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        found = cascade.detectMultiScale(
            gray, scaleFactor=1.1, minNeighbors=5, minSize=(24, 24)
        )
    except cv2.error as exc:
        raise RuntimeError("face_detector_unavailable") from exc
    boxes = []
    for x, y, w, h in found:
        x, y, w, h = map(int, (x, y, w, h))
        if w <= 0 or h <= 0 or x < 0 or y < 0 or x + w > width or y + h > height:
            continue
        boxes.append({"x": x, "y": y, "width": w, "height": h})
    return {
        "state": "analysed",
        "detector": "opencv_haar_frontalface",
        "image": {"width": width, "height": height},
        "face_count": len(boxes),
        "faces": boxes,
        "identity_verified": False,
        "liveness_verified": False,
        "emotion_inferred": False,
        "raw_content_retained": False,
        "continuous_video_proven": False,
        "execution_granted": False,
        "human_authority_final": True,
        "limitations": "Frontal Haar detection can miss faces and produce false positives; count is an estimate.",
    }
