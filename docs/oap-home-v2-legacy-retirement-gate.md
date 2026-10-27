# OAP Home V2 — legacy retirement gate (OFF BY DEFAULT)

Scope: Royal Home V2 `com.onanypostcode.oaphome.v2` and legacy
`com.onanypostcode.oaphome`. This is an operational gate, NOT an uninstall
script, runtime automation, permission grant or proof that a phone was updated.

## Founder-approved sequence
1. **Identify** the *actual* installed package ID, version, signing SHA-256
   and authoritative inventory on the physical Android device.
2. **Update V2 in place** only with the **same** installed-V2 signer, higher
   versionCode, correct package identity, HTTPS/verified APK digest, and
   Android-sanctioned installer approval when required. A different signer
   or a missing receipt blocks the update; do not reset app data.
3. **Prove V2 on device:** cold launch, HOME intent/default selection,
   dock and Koradaso Internet handoff, OAP Store, settings persistence,
   background/foreground, reboot survival and no privacy regression.
4. **Preserve recovery:** GoLauncher stays installed and launchable; Termux
   Home Node and its persistent services/data are out of scope for this
   legacy Android package retirement. Record an explicit recovery test.
5. **Preserve data:** establish whether the old package owns unique data,
   accounts, links, credentials or files. If so, obtain an authorised,
   independently verified migration/backup before proposing removal.
6. **Switch:** Founder confirms the replacement is the active launcher and
   agrees that the identified old package is genuinely redundant.
7. **Retire only after Founder Final:** request **Android's normal user-approved
   uninstall** of `com.onanypostcode.oaphome` only; no silent uninstall,
   no `pm uninstall`, no blanket cleanup and no Termux or GoLauncher removal.
   Confirm removal via device package inventory, then confirm V2 and recovery
   still work.

## Blocking / recovery states
- If any prior gate is unproven: **DO NOT REMOVE LEGACY**.
- If the installed V2 signer cannot be established: **DO NOT INSTALL CANDIDATE**.
- If the original legacy package contains irreplaceable local data:
  **DO NOT REMOVE LEGACY** until migration is separately proven.
- If launcher switching or update fails: use GoLauncher recovery; preserve
  the existing legacy installation and record the failure.
- Retiring a Termux/server node is a **different mission** requiring service,
  DNS, data, persistence, backup and rollback proof, not this Android gate.

## Acceptance evidence required
Record device model, Android version, package IDs, versionCodes,
installed-V2 signing fingerprint, candidate signing fingerprint, APK SHA-256,
install and reboot results, migrated-data checks, GoLauncher recovery result,
and explicit Founder Final approval. Avoid exposing keys, private user data
or passwords in publicly visible logs.

**Current production status: NOT PROVEN; do not trigger uninstall.**
