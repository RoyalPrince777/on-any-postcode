# OAP Store + PTT: self-hosting release contract

Status: **design only — NOT DEPLOYED**. No DNS, host, certificate, secrets, TURN relay, production database, or physical-device proof is implied.

## Reuse (no second app)

- Existing Flask/Gunicorn runtime: `Dockerfile.runtime` (`PORT=10000`).
- Existing public OAP Store `/store`, PTT `/ptt`, and PTT PWA manifest.
- Existing pair-authorized PostgreSQL signalling and migration `migrations/0013_ptt_webrtc_signals.sql`.
- Preserve Founder Final, Guardian, STOP mic shutdown, and fail-closed `/ptt/live/status`.

## Smallest viable target

One hardened Linux host with a public IPv4 address, persistent encrypted storage, and working DNS:
- HTTPS reverse proxy listening on TCP 443 (TCP 80 only for certificate issuance/redirect).
- Existing OAP Flask runtime on an internal network; **never publish Gunicorn port 10000**.
- PostgreSQL on a private container network and persistent volume; **never publish port 5432**.
- Authenticated coturn STUN/TURN with an explicitly configured public IP, TLS where applicable, a narrow UDP relay port range, firewall rules, and short-lived credentials minted server-side.
- External encrypted database backups and a rehearsed restore; version-pinned images, controlled updates, and rollback.

A server administered by OAP is first-party application control, but rented hardware/networking still depends on an infrastructure provider. Home hosting requires stable upstream, public reachability, no blocking CGNAT, and reliable power/networking.

## Security gates BEFORE exposure

1. Verify server ownership and administrative access, SSH keys, least privilege, patched OS, firewall, TLS certificate, and no accidental private OAP/SMI route exposure.
2. Keep secrets in protected runtime configuration (never commit them). Use unique session secret, strong PostgreSQL credentials, TURN shared secret, and encrypted backup keys.
3. Review app-level auth and CSRF, guest invite brute-force/rate limits, session cookie Secure/HttpOnly/SameSite, request limits, logging retention, and IP privacy.
4. Apply and verify **all required existing migrations** against a fresh PostgreSQL database; confirm `oap_ptt_signals` expiry and pair authorization.
5. Wire `RTCPeerConnection` to **authenticated, short-lived OAP-issued TURN credentials**. Current `iceServers: []` is not public-network-ready.
6. Keep `/ptt/live/status` fail-closed until real authenticated signalling, TURN reachability, and cross-network media proof exists.
7. Test STOP immediate mic shutdown, release-to-listen, hangup, reconnect, lost network, permission denial, autoplay recovery, and two Android phones on separate networks.
8. Verify PWA manifest, HTTPS service worker, Android install, offline behaviour, and store-to-PTT launch; record browser/device evidence.
9. Require green CI, reviewed immutable build, health read-back, backup restore, rollback and Founder Final before Green.

## Minimal network policy

- Public: TCP 443; TCP 80 for ACME/redirect if used; TURN listening ports (commonly 3478 UDP/TCP and 5349 TLS) plus an intentionally bounded UDP relay range.
- Private: Flask 10000 and PostgreSQL 5432.
- Restrict SSH to approved administrators/networks.
- TURN must not be an open relay; credential issuance must be rate-limited and bound to an authorized, active pair. Never ship static TURN passwords to browser JavaScript.

## Rollout

1. Code + CI proof (this PR closes missing JS syntax coverage only).
2. Separate reviewed deployment configuration and TURN credential work.
3. Provision chosen OAP-controlled server; validate firewall, secrets, DNS and HTTPS.
4. Run migrations and route acceptance.
5. Run real cross-network two-phone test.
6. Founder Final approval; only then change domain routing and advertise install/live voice.

**Unverified:** host, capacity, pricing, public IP, DNS, live installation, TURN, database, Android voice, and production health. Do not use invented percentages.
