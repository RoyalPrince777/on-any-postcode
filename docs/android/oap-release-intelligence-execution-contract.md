# OAP Release Intelligence — Founder-first execution contract

## Identity
OAP is the sole public product identity. Internal Android package fields,
cryptographic digests and release records remain standards-compatible technical
data, not borrowed product branding.

## Mission
Deliver a first-party, Founder-controlled, fail-closed update path. Preserve the
working OAP Home experience and never auto-install, silently download or treat
a green build as production/device acceptance.

## Best-fit SMI roles (engineering responsibilities, not running agents)
- **Gyata — mission command:** protects Founder Final and upgrade-only scope.
- **Fox — implementation:** joins the update UI, local verifier and release flow.
- **Keymaker — integration:** Android lifecycle, package/archive access, update entry.
- **Seraph — authenticity:** trusted release identity and candidate signing evidence.
- **Bagheera — privacy/security boundaries:** deny unverified installs; least privilege.
- **Oracle — independent proof:** executed CI, negative tests, exact commit evidence.
- **Shere Khan — adversarial challenge:** corrupted APK, spoofed metadata, wrong
  package/version, signer mismatch, rotation and time-of-check/time-of-use.
- **Spider — dependency analysis:** release source, Android signing and installer gates.
- **Queen Bee — coordination only when multiple checks/workers must be reconciled.**
No extra roles solely to enlarge a council. Founder makes final installation choice.

## Evidence on branch
- Streaming SHA-256 helper and local candidate signer comparison exist.
- Local verifier checks manifest package/version against archive package/version,
  digest and installed signer.
- Dedicated contract workflow executes pure-Java eligibility, metadata and
  digest tests. This is not a complete end-to-end Android installer test.
- No verified trusted release channel, governed release attestation, safe staging
  and recheck, consent-driven installer, key-rotation handling or physical device
  acceptance has been established.

## Remaining implementation contract
1. Authenticate a first-party release manifest with a pinned trusted authority,
   not merely a URL or hash delivered by the same untrusted channel.
2. Require an approved exact artifact identity and governed release evidence.
3. Download into app-private staging, bound size, handle interruption, reject
   redirects/untrusted sources and recheck digest after staging.
4. Validate package identity, monotonic version and signing lineage using
   Android-supported mechanisms; handle multiple signers and rotation explicitly
   or block them.
5. Prevent check/use races; verify staged bytes again before presenting an
   installation request. Never bypass the platform installer.
6. Obtain explicit Founder confirmation for each installation; no automatic
   updates or hidden execution.
7. Execute adversarial tests in CI and real physical-device acceptance before
   making any device-ready claim.

## Gate language
- **Committed:** source exists on branch.
- **CI Green:** named workflow passed on the exact commit.
- **Software verified:** relevant tests actually executed and passed.
- **Device accepted:** physical-device checks documented.
- **Production ready:** all required release, security and device gates proven.
Do not substitute one category for another.

## Recovery
Any failed or unknown gate blocks update installation. Leave the existing
working OAP Home installed. Preserve logs without exposing personal data.
