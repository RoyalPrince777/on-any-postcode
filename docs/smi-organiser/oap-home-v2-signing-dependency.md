# SMI Organiser — OAP Home V2 signing dependency

Status: **Pending Founder secure setup**. This is an organisational record, not a deployed organiser application or proof of automated reminders.

## Objective
Provide a persistent signing identity for `com.onanypostcode.oaphome.v2` without changing the installed Build #19 package or weakening release gates.

## Owners
- Founder: securely enter repository secrets and certificate variable.
- Bagheera (proposed security-review role): protect key handling.
- Fox (proposed recovery role): preserve continuity and backups.
- Benji (proposed Android role): validate APK identity and install compatibility.
- Guardian/HRM: enforce human authorisation and evidence requirements.
These are planning assignments, not independently executing agents.

## Required GitHub configuration
Repository secrets: `OAP_HOME_KEYSTORE_B64`, `OAP_HOME_KEYSTORE_PASSWORD`, `OAP_HOME_KEY_ALIAS`, `OAP_HOME_KEY_PASSWORD`.
Repository variable: `OAP_HOME_CERT_SHA256`.
Never put the private keystore, its base64 representation, or passwords in Git, this organiser, chat or logs.

## Resume criteria
1. Founder privately configures GitHub Actions and securely backs up the keystore.
2. Exact-source CI validates the pinned signing certificate and generates an APK for `com.onanypostcode.oaphome.v2`.
3. Verify APK hash, signature, package and device installation separately; do not claim Green early.

## Meanwhile
Continue OAP Home UI, OAP Internet and Virtual Android engineering. Build #19 remains untouched. No changes to Render services or production deployment are authorised by this entry.

Evidence: Java compilation passed in GitHub Actions run 39454855872; signing job failed. Overall VPI: N/A.
