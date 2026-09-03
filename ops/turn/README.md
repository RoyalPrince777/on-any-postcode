# OAP first-party TURN relay v1

This package is the deployable relay boundary for **The Link → Call / Face Up**. It is designed for an OAP-controlled Linux host with its own public IPv4 address and DNS name.

It does **not** make Call or Face Up ready by itself. The application must keep `OAP_LINK_TURN_RELAY_VERIFIED=false` until the external proof in this directory succeeds from a separate network.

## Why this is not deployed as an existing Render web service

Render web services expose public traffic through an HTTP load balancer. Coturn requires browser-reachable TURN traffic, including UDP and raw TURN/TLS, plus a UDP relay port range. Render's arbitrary-protocol ports are private-network ports, so the existing public OAP web-service shape is not a valid public TURN relay boundary.

## Host requirements

- OAP-controlled Linux host with a stable public IPv4 address.
- DNS name such as `turn.<OAP-owned-domain>` resolving directly to that host.
- Coturn installed from the host's maintained package source or a pinned, reviewed Coturn build.
- A valid public TLS certificate for the TURN DNS name.
- Firewall/NAT forwarding for:
  - `3478/udp` — TURN UDP listener.
  - `3478/tcp` — TURN TCP listener.
  - `5349/tcp` — TURN over TLS.
  - `49152:49252/udp` — initial bounded relay allocation range.
- The host must not sit behind a NAT that rewrites or blocks the declared public address without matching port forwarding.

The initial relay range is intentionally narrow. Increase it only with capacity evidence and matching firewall changes.

## Install

Example for a Debian/Ubuntu-style host:

```bash
sudo apt-get update
sudo apt-get install -y coturn
sudo install -d -m 0755 /usr/local/lib/oap-turn
sudo install -d -m 0700 /etc/oap-turn
sudo install -m 0755 ops/turn/start-turn.sh /usr/local/lib/oap-turn/start-turn.sh
sudo install -m 0644 ops/turn/oap-turn.service /etc/systemd/system/oap-turn.service
sudo cp ops/turn/oap-turn.env.example /etc/oap-turn/oap-turn.env
sudo chmod 0600 /etc/oap-turn/oap-turn.env
```

Generate a new secret on the relay host and put it in `/etc/oap-turn/oap-turn.env`:

```bash
openssl rand -base64 48 | tr '+/' '-_' | tr -d '=\n'
```

Use the **same secret** as the server-side `OAP_LINK_TURN_SHARED_SECRET` value in OAP. Never place it in browser code, logs, Git, screenshots, support messages, or monitoring labels.

Set the real realm, public IPv4, certificate and private-key paths, then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now oap-turn
sudo systemctl status oap-turn --no-pager
```

## External certification

Run `verify-turn-external.sh` from a machine on a **different external network**, not from the TURN host or its private LAN. Install the Coturn utilities and OpenSSL on that probe machine, export the TURN hostname and shared secret locally, then run:

```bash
export OAP_TURN_EXTERNAL_PROBE=true
export OAP_TURN_HOST='turn.<OAP-owned-domain>'
export OAP_TURN_SHARED_SECRET='<same server-side secret>'
./ops/turn/verify-turn-external.sh
```

A valid proof must end with:

```text
OAP_TURN_EXTERNAL_RELAY_PROOF_V1_PASS
```

The probe proves UDP relay, TCP transport relay, hostname-valid TLS, and TURN/TLS relay using Coturn's time-limited REST-secret authentication. Do not set `OAP_LINK_TURN_RELAY_VERIFIED=true` unless this proof has passed against the exact production host.

## Application settings after proof

Only after the external proof is recorded should both OAP web services receive matching server-side values:

```text
OAP_LINK_TURN_URLS=turn:turn.<OAP-owned-domain>:3478?transport=udp,turn:turn.<OAP-owned-domain>:3478?transport=tcp,turns:turn.<OAP-owned-domain>:5349?transport=tcp
OAP_LINK_TURN_REALM=turn.<OAP-owned-domain>
OAP_LINK_TURN_SHARED_SECRET=<same secret>
OAP_LINK_TURN_OWNED=true
OAP_LINK_TURN_RELAY_VERIFIED=true
OAP_LINK_TURN_TTL_SECONDS=300
```

Until then, leave the verified flag false or absent. The browser controller will remain locked.

## Privacy and abuse boundary

- REST credentials are short lived and tied to the authenticated OAP identity by the application.
- The permanent shared secret remains server side.
- Multicast peers and common private/reserved IPv4 peer ranges are denied by the launcher.
- Coturn's software-version attribute is disabled.
- The CLI remains disabled by default.
- Relay allocations use a bounded port range and quotas.
- This layer relays encrypted WebRTC transport; it does not record media or create call transcripts.
