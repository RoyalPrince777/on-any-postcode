# SMI Studio Vision — Founder-private face boxes

State: **BUILDING — OFF BY DEFAULT**. This is **not** a production/live-camera certificate.

## Canonical placement

SMI Chat and existing Face Up/Vision controls are **capture** surfaces. OAP Studio Intelligence owns media processing. This adds a bounded, first-party, offline OpenCV Haar frontal-face still-image adapter to Studio; it creates no second brain, Streamlit front door, identity service, face database or automatic camera session.

## API contract (after controlled local opt-in)

- `POST /mission/studio/vision/faces` — the existing Mission Control blueprint.
- Founder authentication required, valid `X-OAP-CSRF` required.
- Disabled by default. Only a deliberately set `OAP_SMI_FACE_DETECTION_ENABLED=true` enables the route in that environment. Do **not** enable it in production without device/security proof and Founder Final.
- A dedicated **7 requests/minute per Founder identity per worker process** burst limit protects CPU-intensive decoding. It does **not** read/cache the face image body to create a request fingerprint, and does not consume the ordinary Chat quota.
- An additional **single concurrent image per worker process** admission semaphore rejects overlapping frames immediately with HTTP **503** `face_detector_busy`, before parsing the queued image; the semaphore is released in a `finally` block on success, invalid input and local-detector failure. The shared admission and disposable worker described below provide additional boundaries; the local slot alone is not a global limit.
- When hosted on **Render** (or when `OAP_SMI_FACE_SHARED_GUARD_REQUIRED=true`), the enabled route also requires `pg_try_advisory_xact_lock(777, 1305)` through the existing **authoritative OAP PostgreSQL** connection. The lock is held throughout decoding/detection and released with the transaction; a busy lock returns 503 `face_detector_busy`, and an unavailable database returns 503 `face_shared_guard_unavailable`, never silently falling back to the local slot. The separate shared quota requires the explicit metadata-only migration described below; no media is written to PostgreSQL.
- The guarded lock coordinates workers using **the same PostgreSQL database**. Non-Render hosts must explicitly enforce the shared guard. A separately committed PostgreSQL upsert reserves **7 attempts per rolling 60 seconds per Founder across workers** before decoding; busy, invalid and timed-out attempts remain charged. Missing quota schema or database access fails closed. SQL statements have a 1.5-second budget; connection establishment uses the existing 5-second connect timeout. Production database connectivity, session-loss behaviour and workload-level measurements still require operational proof before live service.
- Media decoding runs in a disposable POSIX Python subprocess with a **7-second wall deadline, 5-second CPU limit and 512 MiB virtual-address-space cap**. OpenCV uses one thread. The child does not inherit service credential environment variables, uses pipes rather than media files, and has zero core-dump and file-size limits. It still runs under the application OS identity with filesystem access. The parent kills and reaps a timed-out child before releasing admission; unavailable enforcement fails closed. These are child-process limits, not an OS security sandbox or a measured whole-host memory budget. Browser Cancel still cannot guarantee immediate server cancellation.
- Requests without a declared acceptable Content-Length fail closed.
- Accepts JSON: `{"image_data":"data:image/png;base64,..."}` (also genuine JPEG or WebP). Only an explicitly submitted frame, not a camera stream.
- At most 3 MiB decoded bytes, 4 million pixels, or 4096 pixels per side. Format spoofing and invalid images are rejected.
- Returns `image.width`, `image.height`, `face_count`, and `faces` with `x, y, width, height` in original-image pixels.
- No image, embedding, face template, personal name or emotional inference is written to HRM, stored, or returned; response is `Cache-Control: no-store`.
- The ordinary local HTTP request audit retains route/status/timing but does not log the media body. This private face route is **excluded from optional Datadog/external HTTP telemetry**. Host/reverse-proxy access logs and connected infrastructure still require a separate live privacy inspection.
- Face-count and box coordinates are **detector estimates**; neither accuracy/liveness nor identity is certified.
- Invalid images return 400 or 413; missing detector returns 503; off-by-default returns 423. No silent fallback to remote inference.

## Existing SMI Vision browser surface

- The existing selected-image preview adds an explicit **Detect faces** button and a visible OAP Studio server-processing disclosure. Merely selecting/capturing an image does **not** send it to this detector.
- The handler uses the existing `studioFaceDetectUrl` route, same-origin credentials, CSRF and a user-clicked POST. It never starts the camera, requests additional permissions, or processes video frames automatically.
- A locked route reports 423 without pretending detection succeeded. A successful result shows estimated count and pixel coordinates, **not** identity, liveness or emotion.
- While detection is pending, the Detect faces button becomes an explicit **Cancel detection** control. Changing/removing the image, the existing Stop button (when available), or leaving the page also aborts the pending browser request and clears its result. Browser cancellation cannot guarantee that a POST already received by the server stopped processing.
- All existing image-preview changes (ordinary upload, legacy camera file, canonical capture, Studio character-reference selection, or attachment cleanup) invalidate previously displayed boxes through bounded preview-attribute observation. A pending request is also aborted locally; server-side cancellation is not guaranteed. Image replacement itself never triggers an analysis POST.
- Face Up cleanup remains registered across repeated pagehide/back-cache cycles. A hidden document also cancels browser detection and stops camera/microphone tracks, including a late-resolving permission request. Returning to the page does not automatically restart capture. Physical Android lifecycle behaviour remains unverified.
- The selected still is processed on the private OAP Studio **server**, not on the phone. Server privacy, logging and transport require live validation before activation.

## Optional local setup and verification

```sh
pip install -r requirements-vision.txt
python -m pytest -q tests/test_studio_face_detection.py tests/test_studio_face_detection_routes.py tests/test_studio_face_resources.py
# CI only: with OAP_REAL_POSTGRES_PROOF=1 and an isolated authorized
# loopback OAP_PRIMARY_DATABASE_URL, run real multi-process quota/admission:
python -m pytest -q tests/test_studio_face_postgres_admission_integration.py
# Browser certification (requires Playwright + real Chromium):
python tests/smi_vision_face_browser_proof.py
```

The optional dependencies do not modify the base `requirements.txt`. OpenCV uses its packaged Haar Cascade, never downloads model assets at runtime. There is no dependency on external face identification services.

## Explicit quota schema gate

`migrations/0014_studio_vision_quota.sql` must be reviewed and applied explicitly to the selected OAP database before hosted verification. No request, import or application startup applies this migration. Missing schema blocks processing. Rollback is feature flag OFF first; retaining or removing the quota table is a separate database decision.

The table contains only authenticated Founder UUID and at most seven attempt timestamps, with no media, hash, boxes or inferred identity. Expired timestamps are replaced on the next attempt; idle rows are not automatically erased. This is bounded operational metadata retention, **not ZERO TRACE certification**. The PostgreSQL tests create and clean fixture quota data only on an explicitly selected loopback CI database.

## Proof gaps before Green Gate

- Full-repository CI and real Chromium acceptance must pass on the exact final head; browser implementation alone is not certification.
- Face Up camera/microphone now inherit the canonical SMI human STOP and browser pagehide boundary. Pending getUserMedia permission requests are invalidated with a generation guard; if a late stream resolves, both tracks are immediately stopped. The real Chromium proof checks End, STOP, repeated pagehide and hidden-document cleanup with controlled simulated permission timing. **No physical Android device test has been claimed.**
- A real authenticated non-fixture Founder browser/device path, plus camera/mic permission denial, background/relaunch and first-party transport evidence.
- Real Founder-device consent/STOP/relaunch/permission-denial evidence and latency/memory checks.
- Detection quality checks with appropriately consented diverse faces and non-face images, including false positives, misses and lighting/pose limitations.
- Security review of crafted media decoding, dependency vulnerability scanning, audit/release evidence and Founder Final.
- Real-host shared-guard deployment proof, process termination/database-session-loss recovery, replica-wide quota confirmation, and measured application/database latency and memory budgets. The CI tests use independent application processes with fixture authentication and cannot establish deployed HTTPS readiness. Abrupt loss of the database lock session while native work continues remains an operational boundary to resolve; a processing deadline does not prove uninterrupted global exclusion.

Continuous video, emotion detection, recognition, attendance, biometric login and automatic background recording are **out of scope and not authorised** by this capability.
