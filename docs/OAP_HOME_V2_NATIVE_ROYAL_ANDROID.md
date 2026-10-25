# OAP Home V2 — Native Royal Android Home

**Founder-final design direction:** Keep the **existing V2 Android app** and
rename its visible icon to **OAP Home**. Retire the old Home app only after the
native V2 app is signed, installed, working and selected as Home, with
independent stock-launcher recovery proven.

Status: **V2 source and source-level Android compile under review.**
Nothing was installed, renamed on-device, uninstalled or made the default Home.

## The two Android packages — do not conflate them

| Identity | Android package | Direction |
|---|---|---|
| Keep and improve | `com.onanypostcode.oaphome.v2` | Royal V2 UI, Android label **OAP Home**, `HOME` role |
| Legacy to retire | `com.onanypostcode.oaphome` | Remove only after V2 accepted and protected data/recovery checked |
| Separate browser | `com.onanypostcode.oapworld` | OAP Internet, does not replace or embed the Home screen |

The earlier review mistakenly changed the V2 Gradle `applicationId` to the
legacy app's package. That has been reversed. **Renaming the app label must
never change the established V2 package or overwrite the old app.** Android
treats the packages as distinct applications until the legacy one is removed.

## Native V2 UI

`android/oaphome` retains the original V2 Java namespace, MainActivity,
Android HOME/DEFAULT intent filters, Store/PTT navigation and user-controlled
default-Home recovery route.

`RoyalHomeArt.java` provides native Canvas gold Earth art and nine tile
illustrations rather than rendering the Home screen through Brave or Flask.
The UI includes native local/world clocks; weather and calendar correctly
display NOT CONNECTED pending live first-party proof.

The Internet dock calls the separate installed OAP Internet package. This
must fail closed when Internet is missing, not open a third-party browser in
disguise. The separate Termux SMI Home Node is neither the launcher nor
controlled by Home V2. A fully independent AOSP **OAP OS** image is not built.

## Same existing V2 — signing and version proof

- Keep V2 `applicationId 'com.onanypostcode.oaphome.v2'`, with candidate
  `versionCode 21` and `versionName '2.1.0-founder-royal'`.
  Version 21 is a **candidate**, not proof it exceeds the installed V2 code.
- The visible `android:label` is **OAP Home**, not **OAP Home V2**.
- The signed APK workflow requires a pinned `OAP_HOME_V2_CERT_SHA256` from
  the installed V2 app and an equal persistent-keystore and candidate signer.
  Any missing proof or certificate mismatch blocks APK artifact publication.
- Run the **read-only** `scripts/oap_home_v2_inplace_apk_gate.py` against
  trusted, verifiable copies of the installed V2 and candidate V2 APKs.
  The gate rejects the legacy package, mismatched signers, outdated versions
  and any candidate labelled differently from OAP Home.
- The signing key used for **old Home** is irrelevant to updating V2.
  The candidate must match the *installed V2* signing identity.
- No debug-key substitution, forced install, data clear, or uninstall of V2.

## Exact device migration and removal order — no automatic uninstall

1. **Inspect, without mutating:** distinguish old and V2 packages, installed
   version codes, APK signers, app data implications and which launcher Android
   currently uses. Verify there is an accessible stock system launcher.
2. **Verify V2 build:** exact SHA, successful native compilation and tests,
   compatible signed V2 APK and candidate > installed V2 version code.
3. **Install/update V2 only** after evidence-based approval; confirm native
   Royal Home UI, stable application drawer, Phone, Messages, Camera, Store,
   PTT and OAP Internet handoff. Do not remove the old app yet.
4. **Switch normal Android Home to V2** through Android Settings >
   Apps > Default apps > Home app. Verify that Home gesture/button opens
   the native OAP royal screen, not Brave. Check return to the stock launcher.
5. **Retire old Home** only once V2 is independently stable, is the selected
   default and its old data are known to be unnecessary or backed up. Confirm
   the exact old **`com.onanypostcode.oaphome`** application in Android
   Settings > Apps before choosing **Uninstall**. Never uninstall
   **`com.onanypostcode.oaphome.v2`** or the Android stock launcher.
   A previous default app can leave Android without the intended launcher
   selection; verify the resulting Home choice and reboot recovery.
6. **Founder Final and Green** only with physical Redmi A5 proof, package
   identities, signer/rollback evidence, and no private Home Node damage.

If the old Home is not installed, there is nothing to remove.
**Green, install completed, legacy removed and final OS readiness: NOT PROVEN.**

## Runtime branches and conflict boundary

The separate Flask review copy at `~/oap-v2-review` remains a visual/web
reference only. Do not reset or merge into the protected
`~/on-any-postcode` Home Node checkout.

PR #1316 targets the existing native source branch
`oap-home-apk-master777`. Its older workflow conflicts with a separate
APK workflow added on current `main`; resolving that integration
conflict remains a separate mandatory governance check. The exact native
compile can pass while whole-repository governance still fails.
