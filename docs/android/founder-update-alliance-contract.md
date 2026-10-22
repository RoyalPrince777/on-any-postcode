# OAP Android Founder Update Centre — SMI Alliance Contract

Status: architecture and policy contract only. Not runtime agents, not a verified updater.

## Authority
Founder Final. Updates are manual and opt-in. No agent can grant itself Android installation privileges, silently install an APK, weaken signature checks, access another user's data, or declare a pending CI job green.

## Alliance responsibilities (logical roles, not running agents)
- **Gyata:** final mission command and Founder decision boundary.
- **Fox:** locate the latest approved release, identify broken links, and propose recovery.
- **Seraph:** validate app identity, installed signing certificate continuity, and permission boundaries.
- **Bagheera:** enforce fail-closed download, integrity, transport, and permission policies.
- **Keymaker:** integrate version metadata, install handoff, and compatibility checks.
- **Oracle:** verify CI and independent evidence; distinguish unknown, pending, pass, and fail.
- **Elephant:** preserve release provenance, checksums, approval and installation audit records.
- **Spider:** track release-to-build-to-artifact dependency lineage.
- **Shere Khan / Agent Smith:** adversarially test spoofed releases, downgrade, rollback, tampering and signing-key mismatch.
- **Queen Bee / Swarm:** coordinate only authorised bounded checks and retries; no autonomous installation.
- **Octopus:** coordinate workflow dependencies without bypassing gates.
- **Neo:** implement and test the approved bounded code changes.

## Required fail-closed update path
1. Read installed version and package identity locally.
2. Query only a pinned first-party release source; no arbitrary URL or redirect trust.
3. Fetch authenticated version metadata with version code, package ID, artifact digest, signing identity and release provenance.
4. Compare version codes; reject downgrade and mismatched package.
5. Check source release, build provenance and current security gate evidence.
6. Download only on explicit Founder request into private temporary storage.
7. Verify SHA-256 and Android signing certificate compatibility against installed app before requesting installation.
8. Present version, permissions, release notes, size and verification results for explicit Founder approval.
9. Hand off to Android's supported user-confirmed package installer; no silent install.
10. After install, confirm installed package/version and preserve an audit record; never claim automatic rollback or data preservation without tested evidence.

## Current engineering boundary
- Native Founder Update Centre screen and menu entry committed.
- Link to repository releases is navigation only; it is not a verified release feed.
- No implemented update manifest, release verification, APK download, install, rollback, or running agent workers.
- CI status must be checked per exact commit; APK build success is not physical-device acceptance.
- Guardian's personal-data and Founder-accountability protocols remain separately gated.

## Acceptance tests required
- Unknown/unavailable release => no install offer.
- Tampered digest or signing identity => reject.
- Same/older version => no upgrade.
- Different package ID => reject.
- Untrusted redirect => reject.
- Unapproved or pending governed checks => reject.
- Cancel => no download or install.
- Android install refusal => report not installed.
- Process death, network loss and insufficient storage => safe recovery.
- Installed app and settings survive an approved update => verify on device.

No fake green. Upgrade only. Founder Final.
