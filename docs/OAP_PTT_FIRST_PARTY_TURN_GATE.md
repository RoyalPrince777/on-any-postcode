# OAP PTT — first-party TURN admission gate

**Status:** bounded code change; **not deployed and not certified live audio**. PTT's
`/ptt/live/status` must continue returning `live_ready: false`,
`signalling_ready: false` and `media_ready: false` until the independent
production release requirements below have actual receipts.

## Reuse the existing OAP-owned service

PTT must not add an independent TURN authority or third-party relay. Reuse:

- `mission_control/link_turn.py` — coturn REST-secret HMAC issuance, 60–900-second
  TTL, server-only `OAP_LINK_TURN_SHARED_SECRET`, OAP-owned URL checks and
  explicit `OAP_LINK_TURN_RELAY_VERIFIED` operator flag.
- `ops/turn/` — the existing first-party coturn host unit, launcher and
  external-network verification script.
- `link_relationships.accepted_between()` and `linkup_safety.blocked_between()`
  — accepted, unexpired Link / block rules. Temporary PTT guest pairs are
  represented as purpose Links and expire without creating a separate media
  permission system.
- `mission_control/ptt_guest.py` — existing 8-digit temporary pairing and
  session-scoped guest identity.
- `mission_control/ptt_signalling.py` — existing peer-bound negotiation
  messages; this change does not add media storage, recording or transcript.

The `POST /ptt/live/ice` route requires the guest session, OAP-CSRF header,
existing rate limiter, a currently active guest pair, a configured verified
OAP-owned relay and existing accepted Link / block checks. Success returns only
time-limited ICE server credentials. Missing proof, expired pairing, blocked
peers and infrastructure errors fail closed; responses use `Cache-Control:
no-store`. Unverified relay returns 503 without credentials.

The browser requests those credentials *before* asking for microphone
permission, and fails closed if the response is unverified or has no ICE server.
The local microphone stays disabled until an actual WebRTC connection and
a user-held HOLD. Release mutes; STOP stops local tracks, destroys the peer and
sends a hangup signal. This code does not establish that a relay is reachable.

## Evidence required for a real live PTT release

1. **OAP-controlled Linux relay host**, public routing, DNS, TLS cert,
   configured coturn credentials, relay firewall/NAT rules and private
   `OAP_LINK_TURN_SHARED_SECRET`. Do not insert real secrets in Git, screenshots
   or public test output. Existing Render HTTP apps cannot replace TURN's
   public UDP relay sockets.
2. Execute `ops/turn/verify-turn-external.sh` from a *different external
   network*, preserve the exact host and timestamped evidence, and require
   `OAP_TURN_EXTERNAL_RELAY_PROOF_V1_PASS` before setting the
   `OAP_LINK_TURN_RELAY_VERIFIED=true` operator flag. The environment flag
   is an operator assertion, **not independent proof** by itself.
3. Check that PostgreSQL migration
   `migrations/0013_ptt_webrtc_signals.sql` has actually run against the
   deployment, and that both guest sessions have separate cookies, pairing
   and CSRF values. Validate active-pair expiry and blocked-peer denial.
4. Use **two physical Android phones on different networks** (e.g. mobile
   data vs Wi-Fi) to prove audible two-way WebRTC media and ICE candidate
   connectivity through the OAP relay. Capture only consented diagnostics,
   never microphone recordings by default. Include headphones/speaker routing.
5. On both devices, verify HOLD-to-talk, release-immediate-mute,
   simultaneous-operation collision handling, STOP-microphone-track shutdown,
   background / network loss, pairing expiry, retry and no retained audio.
   Reverify when the short-lived credential expires or ICE must restart.
6. Only then review deployed revision, health, rollback, Guardian/permission
   status and Founder Final. Upgrade `/ptt/live/status` to a true
   independently evidenced readiness projection in a separate bounded change.
   Do **not** turn that boolean on in this PR.

## Automated scope

Dedicated `OAP PTT proof` workflow compiles and lints PTT code, checks the
browser client and runs its Node event-control test, verifies Flask endpoint
CSRF/pair/relay denial behavior, checks the reused Link Turn issuer and runs
the existing PTT regressions. These checks verify software behavior in CI and
**never substitute for real TURN host and two-device proof**.

Historical references: PR #1300 (SMI War Room and initial PTT reconnection),
PR #1301 (CSRF fix), and PR #1296 (separate, overlapping self-host/CI draft —
review its overlap before merging).
