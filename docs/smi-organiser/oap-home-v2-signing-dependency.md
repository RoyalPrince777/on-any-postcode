# SMI Organiser — OAP Home V2 in-place signing dependency

Status: **BLOCKED pending certificate evidence from installed original Home**.
This is an organisational record, not a deployed organiser or automatic installation.

## Founder decision
**One OAP Home icon and one Android Home destination**, running the upgraded
Royal V2 native interface with original package identity
`com.onanypostcode.oaphome`. Its visible name remains **OAP Home**.
Do not create or install `com.onanypostcode.oaphome.v2` as a second launcher.

Keep the original Build #19 installed and all existing app/Termux/Home Node data
intact until a compatible, version-increasing in-place replacement is proven.
A valid Android update supersedes old app code **without an uninstall**.

## Required proof (not currently established)
1. Safely identify the currently installed original OAP Home APK, package ID,
   Android versionCode, and signer certificate fingerprint. A build number
   printed in a prior conversation does not certify the on-device versionCode.
2. Confirm the intended persistent signing keystore matches the installed
   original APK certificate. The prior V2-only keystore
   (`~/oap-private/oap-home-v2.jks`, alias `oap-home-v2`) **cannot be assumed**
   compatible with Build #19.
3. Configure `OAP_HOME_ORIGINAL_CERT_SHA256` as a GitHub Actions variable
   only from independently verified original APK evidence. Retain the protected
   signing secrets `OAP_HOME_KEYSTORE_BASE64`,
   `OAP_HOME_KEYSTORE_PASSWORD`, `OAP_HOME_KEY_ALIAS`, and
   `OAP_HOME_KEY_PASSWORD`. Never paste secrets in chat, logs or Git.
4. Build the exact updated native branch and prove its APK signer equals that
   original certificate before artifact publication. Independently apply
   `scripts/oap_home_v2_inplace_apk_gate.py` to verified copies of the old
   installed APK and candidate APK: matching package, matching signer, strictly
   increasing versionCode, user-facing label **OAP Home**.
5. Device test on the Redmi A5 with backup/recovery ability: installed original
   app data and Android Home choice intact, V2 royal UI, installed app drawer,
   Phone/Messages, separate OAP Internet app, Store/PTT and settings recovery.
   No flash, no default-launcher switch without the user's own action.

Any mismatch or missing evidence = **BLOCK**, not an excuse to uninstall the
old app. A separate `.v2` install would create a second Home candidate and
contradict the current Founder direction.

## Boundaries
This upgrade does not replace Android's operating system or change the
independent OAP Home Node supervisor. `OAP OS` remains the future
independently verified AOSP target.

No Android APK, Home selection, data migration or build-signature continuity is
claimed until physical device evidence and Founder Final are supplied.
Overall VPI: N/A.
