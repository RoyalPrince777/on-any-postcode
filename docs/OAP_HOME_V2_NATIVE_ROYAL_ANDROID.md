# OAP Home V2 · Native Android Royal Alignment

Status: **Native Android source upgrade under review. Not installed, not device-certified, not OAP OS.**

## Founder product distinction

- **OAP Home V2:** existing native Android Home launcher project at `android/oaphome/`,
  built as an **in-place upgrade to the original OAP Home Android app**
  `com.onanypostcode.oaphome`, with the visible name **OAP Home** (V2 is the implementation version, not a second icon).
  Android `CATEGORY_HOME` and `CATEGORY_DEFAULT` preserve its role in the
  same system Home destination. It must not install a competing
  `com.onanypostcode.oaphome.v2` app. The currently installed package must
  have a matching signer, an older Android versionCode and a verified rollback
  plan; **do not uninstall Build #19 or delete its data**. The user chooses
  the default Home app; no device-owner powers are taken.
- **OAP Internet:** separate Android browser application
  `com.onanypostcode.oapworld`, not an in-app browser disguised as a Home
  screen. The Home dock opens that package only when installed, with an
  unavailable explanation otherwise.
- **OAP Home Node:** separate supervised Termux SMI/organism runtime. No
  supervisor, credentials or processes are touched by the native UI build.
- **OAP World / services:** distinct public services with their own HTTPS and
  identity boundaries. Some existing destination cards still route to a
  bounded web-powered content viewer after native Home navigation; this
  is not evidence of fully native equivalents for all public apps.
- **OAP OS:** future independently built and verified AOSP-based OS image with
  drivers, boot/recovery and security integration. A launcher APK is not an OS.

## Visual reference and actual source

The Founder-approved 2026-10-25 gold Earth reference remains the master visual
direction. The existing native `MainActivity.home()` is upgraded with Android
Views and `RoyalHomeArt.java` Canvas drawing, rather than rendering
`/home-v2` through Flask or Brave.

- Royal OAP header with local gold-lit Earth artwork and two-line slogan.
- Real device date/time and IANA-zone city clocks. No pretend live weather or
  calendar feeds.
- Nine illustrated 3-column app cards: World, Link Up, SIKA; Maps, Mail, Market;
  TV, Arena, Library.
- Phone / Messages / Internet / Camera / Apps dock.
- Standalone PTT and OAP Store remain directly accessible.
- Android Settings and user-controlled Default Home selection allow return to
  the stock launcher. User chooses changes; no auto-enrolment.
- Artwork is a source-aligned approximation, not yet pixel-identical to the
  original image or visually accepted on the device.

## Safety and proof

1. Compile the modified exact `android/oaphome` source with Android SDK 35,
   Gradle 8.11.1 and Java 17. Static tests independently check HOME intent,
   canonical package IDs and fail-closed missing Internet handoff.
2. Keep the original installed `com.onanypostcode.oaphome` package intact
   until its actual APK identity, signer SHA-256 and versionCode are known.
   The upgraded V2 is `com.onanypostcode.oaphome` with versionCode 21;
   this number is a **source candidate**, not proof it is newer than the
   installed Build #19. Do not publish an APK signed with the newer V2-only
   keystore if that differs from the old APK's signer.
3. Before any update, run the **read-only** `scripts/oap_home_v2_inplace_apk_gate.py`
   against a verified copy of the installed original APK and the exact
   release candidate APK. The gate checks identical package ID, exact signer,
   strictly higher versionCode and `OAP Home` visible app name. Missing
   evidence, missing `aapt` or `apksigner`, signer mismatch or downgrade
   **blocks installation**. The existing signing workflow has not established
   same-signer identity with Build #19 and must not be treated as a release.
   Never uninstall the old Home, clear data, change the stock launcher, or
   overwrite local Home Node files to make a test succeed.
4. On a real Redmi A5, install without changing the default Home app first;
   prove launch, touch, installed apps drawer, dialler, camera, OAP Internet
   missing/present behaviour, navigation, status/navigation bars and reboot
   recovery. If the user elects to set OAP Home as the default, confirm stock
   Home recovery via Android Settings → Default apps → Home app.
5. Only after exact-artifact device tests, Guardian/Aegis and Founder Final
   may a release or OAP OS readiness claim be made.

The separate `~/oap-v2-review` Flask worktree remains a visual/web
reference only. It must not be mistaken for the native Home APK or the OS image.
