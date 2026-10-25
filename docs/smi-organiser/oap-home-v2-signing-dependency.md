# SMI Organiser — Existing V2 Home signing and legacy Home retirement

**Status:** Release blocked pending on-device signer/version and Home recovery evidence.
This is a planning/evidence record, not an installed app, background worker
or uninstall authorisation.

## Founder decision: keep V2, rename V2, retire the OLD Home

The app to **retain** and upgrade is `com.onanypostcode.oaphome.v2`.
Its **visible name becomes OAP Home**. Preserve its Android HOME role and
user-selected default Home destination.

The **legacy** app is `com.onanypostcode.oaphome`. Retire it *only after*
verified V2 functionality, selection as default Home and safe stock Home
recovery. Do not swap the package IDs, do not install another competing
launcher and do not silently uninstall any app.

## Source/build prerequisites

1. Identify the installed V2 versionCode and signing SHA-256 and verify a
   safe copy of the existing APK. Do not assume earlier Build #19 refers
   to the same package or has a particular Android versionCode.
2. Require the **installed V2 certificate** fingerprint as the GitHub Actions
   variable `OAP_HOME_V2_CERT_SHA256`. The separate old-Home certificate
   must not be used to sign or certify V2. The existing protected signing
   keystore and alias must match that V2 fingerprint.
3. Existing signing secrets remain
   `OAP_HOME_KEYSTORE_BASE64`, `OAP_HOME_KEYSTORE_PASSWORD`,
   `OAP_HOME_KEY_ALIAS` and `OAP_HOME_KEY_PASSWORD`. Never paste a
   keystore, base64 secret or passwords into chat, source or logs.
4. The exact APK must identify `com.onanypostcode.oaphome.v2`, have a
   higher versionCode, display `OAP Home` and prove the installed V2
   signer matches. `scripts/oap_home_v2_inplace_apk_gate.py` is the
   **read-only** offline comparison; no install/uninstall action.
5. Test V2 native HOME startup, all required dock/navigation controls,
   no Brave substitution, secure OAP Internet app handoff, data persistence,
   and Android default-Home/stock-launcher recovery on Redmi A5.
6. Only then may the Founder choose to retire the exact
   `com.onanypostcode.oaphome` legacy app in Android Settings. Inspect
   the app identity and app-data implications first; never uninstall
   `com.onanypostcode.oaphome.v2`, the Android system launcher, Termux
   or Home Node.

## Until verified

The Android APK artifact, removal of the legacy Home, V2 default-launcher
switch, device acceptance, future first-party OS image and Founder Final
remain unverified and must not be labelled complete. Overall VPI: N/A.
