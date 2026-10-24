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

## Existing SMI Vision browser surface

- The existing selected-image preview adds an explicit **Detect faces** button and a visible OAP Studio server-processing disclosure. Merely selecting/capturing an image does **not** send it to this detector.
- The handler uses the existing `studioFaceDetectUrl` route, same-origin credentials, CSRF and a user-clicked POST. It never starts the camera, requests additional permissions, or processes video frames automatically.
- A locked route reports 423 without pretending detection succeeded. A successful result shows estimated count and pixel coordinates, **not** identity, liveness or emotion.
- Changing/removing the image, the existing Stop button, or leaving the page aborts the pending browser request and clears its result. Browser cancellation cannot guarantee that a POST already received by the server stopped processing.
- The selected still is processed on the private OAP Studio **server**, not on the phone. Server privacy, logging and transport require live validation before activation.

## Optional local setup and verification

```sh
pip install -r requirements-vision.txt
python -m pytest -q tests/test_studio_face_detection.py tests/test_studio_face_detection_routes.py
# Browser certification (requires Playwright + real Chromium):
python tests/smi_vision_face_browser_proof.py
```

The optional dependencies do not modify the base `requirements.txt`. OpenCV uses its packaged Haar Cascade, never downloads model assets at runtime. There is no dependency on external face identification services.

## Proof gaps before Green Gate

- Full-repository CI and real Chromium acceptance must pass on the exact final head; browser implementation alone is not certification.
- A real authenticated non-fixture Founder browser/device path, plus UI failure/cancellation and first-party transport evidence.
- Real Founder-device consent/STOP/relaunch/permission-denial evidence and latency/memory checks.
- Detection quality checks with appropriately consented diverse faces and non-face images, including false positives, misses and lighting/pose limitations.
- Security review of crafted media decoding, dependency vulnerability scanning, audit/release evidence and Founder Final.

Continuous video, emotion detection, recognition, attendance, biometric login and automatic background recording are **out of scope and not authorised** by this capability.
