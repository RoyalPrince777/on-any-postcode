"""Founder-private still-image face boxes for canonical OAP Studio Vision.

No identity inference, liveness proof, frame storage, network calls, or implicit
camera access. The caller owns authorisation, CSRF and request-rate boundaries.
"""
from __future__ import annotations

import base64
import binascii
import re
from io import BytesIO
from typing import Any

MAX_IMAGE_BYTES = 3 * 1024 * 1024
MAX_IMAGE_PIXELS = 4_000_000
MAX_IMAGE_SIDE = 4096
_DATA_URL = re.compile(r"\Adata:(image/(?:jpeg|png|webp));base64,([A-Za-z0-9+/=]+)\Z", re.IGNORECASE)
_FORMATS = {"image/jpeg": "JPEG", "image/png": "PNG", "image/webp": "WEBP"}


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
