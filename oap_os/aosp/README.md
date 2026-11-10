# OAP OS AOSP product integration overlay (pre-boot)

This overlay is for an AOSP source checkout on a supported Linux build host.
It is not an OS image and does not imply the application is already integrated.

## Integration contract

1. Build the existing `android/oapworld` APK from a pinned commit; verify SHA-256 and package name `com.onanypostcode.oapworld`.
2. Copy the reviewed APK to `vendor/oap/prebuilt/OapWorld.apk` in the AOSP checkout.
3. Copy the `vendor/oap` files from this directory to that checkout.
4. Include `vendor/oap/oap_product.mk` from a custom emulator product makefile, not the global AOSP base product.
5. Build and boot an emulator image before claiming integration success.

The APK is initially a **non-privileged system application**. No platform signature, privileged permissions, device-owner powers or SELinux exceptions are granted.

## Boot evidence

Record the emulator target and AOSP revision, system image hashes, emulator boot logs, `adb shell getprop sys.boot_completed`, `adb shell pm path com.onanypostcode.oapworld`, and an OAP World launch screenshot.

## Security gates

Check SELinux enforcing, no elevated app privileges, restricted file/content access, network transport and HTTPS policies, package signing, update path, and emulator wipe/recovery. Do not use permissive SELinux to make boot pass.
