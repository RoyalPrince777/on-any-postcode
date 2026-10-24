# SMI Studio Vision — Founder-private face boxes

State: **BUILDING — OFF BY DEFAULT**. This is **not** a production/live-camera certificate.

## Canonical placement

SMI Chat and existing Face Up/Vision controls are **capture** surfaces. OAP Studio Intelligence owns media processing. This adds a bounded, first-party, offline OpenCV Haar frontal-face still-image adapter to Studio; it creates no second brain, Streamlit front door, identity service, face database or automatic camera session.

## API contract (after controlled local opt-in)

- `POST /mission/studio/vision/faces` — the existing Mission Control blueprint.
- Founder authentication required, valid `X-OAP-CSRF` required.
- Disabled by default. Only a deliberately set `OAP_SMI_FACE_DETECTION_ENABLED=true` enables the route in that environment. Do **not** enable it in production without device/security proof and Founder Final.
- The existing SMI chat burst limiter applies. Requests without a declared acceptable Content-Length fail closed.
- Accepts JSON: `{"image_data":"data:image/png;base64,..."}` (also genuine JPEG or WebP). Only an explicitly submitted frame, not a camera stream.
- At most 3 MiB decoded bytes, 4 million pixels, or 4096 pixels per side. Format spoofing and invalid images are rejected.
- Returns `image.width`, `image.height`, `face_count`, and `faces` with `x, y, width, height` in original-image pixels.
- No image, embedding, face template, personal name or emotional inference is written to HRM, stored, or returned; response is `Cache-Control: no-store`.
- Face-count and box coordinates are **detector estimates**; neither accuracy/liveness nor identity is certified.
- Invalid images return 400 or 413; missing detector returns 503; off-by-default returns 423. No silent fallback to remote inference.

## Optional local setup and verification

```sh
pip install -r requirements-vision.txt
python -m pytest -q tests/test_studio_face_detection.py
```

The optional dependencies do not modify the base `requirements.txt`. OpenCV uses its packaged Haar Cascade, never downloads model assets at runtime. There is no dependency on external face identification services.

## Proof gaps before Green Gate

- Full-repository CI, private route access/CSRF/rate-limit integration tests, full API response validation under Flask.
- Browser UI wiring to the existing user-initiated Vision capture control **without** expanding camera permissions.
- Real Founder-device consent/STOP/relaunch/permission-denial evidence and latency/memory checks.
- Detection quality checks with appropriately consented diverse faces and non-face images, including false positives, misses and lighting/pose limitations.
- Security review of crafted media decoding, dependency vulnerability scanning, audit/release evidence and Founder Final.

Continuous video, emotion detection, recognition, attendance, biometric login and automatic background recording are **out of scope and not authorised** by this capability.
