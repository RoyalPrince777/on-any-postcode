# OAP OS — AOSP emulator integration gate

Status: SOURCE INTEGRATION PREPARATION ONLY. No OAP OS system image has been built or booted.

## Separation of products

- OAP Internet: browser surface and navigation.
- OAP Android: installable APK built from `android/oapworld`.
- OAP OS: future AOSP-based system image, NOT an APK or launcher rebrand.

## Required external build prerequisites

A dedicated Linux build machine with adequate disk, RAM, supported JDK/toolchain, Android `repo` tooling and a pinned AOSP manifest. A phone or Termux alone is not an adequate substitute for an AOSP build host.

## Emulator-first integration gate

1. Record exact AOSP manifest revision and build host details in a build receipt.
2. Sync official AOSP sources; use an emulator-compatible target (Cuttlefish or AOSP emulator as supported by the chosen branch).
3. Build an unmodified baseline image and capture logs and artifact hashes.
4. Integrate OAP Android as a system app only after baseline boot proof; configure OAP Home separately.
5. Build a new image and boot in an emulator; record `adb devices`, `getprop sys.boot_completed`, boot logs, and screenshot evidence.
6. Verify SELinux enforcing, app sandbox/permissions, verified-boot capabilities for the selected emulator target, network boundaries, updates, and recovery.
7. Keep physical flashing, bootloader unlock and release signing outside this gate.

## Honest evidence states

- Source preparation: documented (this file).
- AOSP source checkout and integration: NOT VERIFIED.
- OAP OS image: NOT BUILT.
- First boot: NOT PROVEN.
- Security and recovery: NOT TESTED.

Never mark any of these Green solely because the OAP Android APK compiles.
