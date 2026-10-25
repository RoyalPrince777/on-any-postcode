# KORADASO Internet — Royal Edition icon & UX

**Founder-selected brand:** BEGORO-KORADASO Internet, short app label **KORADASO Internet**.
**Parent:** ON ANY POSTCODE. **Browser home:** `/world`. **Private Founder SMI:** separate.

## Exact-artwork provenance
- The Android browser icon is a **cropped and resized derivative of the Founder-selected KORADASO Royal Edition 1254 × 1254 master artwork**, not a newly reinterpreted logo.
- The square icon isolates the existing gold diamond crown, K and globe, keeping the original lettering/master image unchanged.
- Android resource: `android/oapworld/src/main/res/drawable-nodpi/koradaso_royal_icon.webp`.
- 128 × 128 WebP source bytes, SHA-256 `30e19b2d561afa0aab48fdfe704313ee0a299e38e3d648da4a865378f8c3bdf3`.
- The full-size master artwork is **not** embedded in the Android APK by this change. No new logo is invented.

## UI/UX
- Native browser launcher now has the separate KORADASO Internet label and custom cropped crest.
- A short royal header displays the crest, `KORADASO INTERNET`, `POWERED BY ON ANY POSTCODE` and origin trust state.
- Keep the existing back/home/omnibox controls and /world as the actual homepage.
- `OAP WORLD` and `OPEN WEB` trust text is calculated from the displayed HTTPS origin; host, scheme, port and credentials must be validated.
- No camera, microphone, location, or private-SMI permission is added.
- This is **not OAP Home V2**, OAP OS or a new installed app/package. Package identity remains unchanged.
- Existing separate PR #1228 contains browser menu work; reconcile its overlap with MainActivity before merge; do not take both versions without integration tests.

## Required launch proof
1. Verify the icon asset SHA-256 and manifest with `pytest tests/test_koradaso_royal_android_identity.py -q`.
2. Build **debug APK** through existing `OAP Android APK` workflow and record APK SHA-256; debug builds are not release signing.
3. Physically install on an Android device, inspect the masked home icon and readability, and check Android dark/light launcher backgrounds and system splash.
4. Check 320dp and Redmi A5 layouts, screen reader descriptions, font scaling, Back and Home, and existing browser navigation.
5. Confirm `OAP WORLD` only for the exact first-party HTTPS origin, and `OPEN WEB` for external domains, redirects, wrong ports and lookalikes.
6. Before real rollout replace the **historic hardcoded Render origin** only when a separately verified non-Render first-party HTTPS destination exists. Do not invent a domain or bypass Founder Final.
7. Do not claim app release, browser completeness, native-engine certification or worldwide availability from CI alone.

**Founder Final remains required; no APK install, service deployment or production mutation is executed in this PR.**
