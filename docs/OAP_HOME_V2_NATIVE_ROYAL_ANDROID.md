# OAP Home V2 · Native Android Royal Alignment

Status: **Native Android source upgrade under review. Not installed, not device-certified, not OAP OS.**

## Founder product distinction

- **OAP Home V2:** existing native Android Home launcher project at `android/oaphome/`,
  package `com.onanypostcode.oaphome.v2`. Android `CATEGORY_HOME` and
  `CATEGORY_DEFAULT` let the user *choose* it as their Home app. OAP does not
  silently change the phone's launcher or obtain device-owner powers.
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
2. Build an APK through the existing *persistent signing* process. The legacy
   `oap-home-apk.yml` intentionally builds from
   `oap-home-apk-master777`; its historical green runs **do not** prove this
   unmerged branch. No debug-signature switch is permitted for a device update.
3. Verify existing installed V1/V2 package identity, Android signature and
   versionCode before any attempted update. Never uninstall stock launchers,
   clear data or overwrite local Home Node files.
4. On a real Redmi A5, install without changing the default Home app first;
   prove launch, touch, installed apps drawer, dialler, camera, OAP Internet
   missing/present behaviour, navigation, status/navigation bars and reboot
   recovery. If the user elects to set OAP Home as the default, confirm stock
   Home recovery via Android Settings → Default apps → Home app.
5. Only after exact-artifact device tests, Guardian/Aegis and Founder Final
   may a release or OAP OS readiness claim be made.

The separate `~/oap-v2-review` Flask worktree remains a visual/web
reference only. It must not be mistaken for the native Home APK or the OS image.
