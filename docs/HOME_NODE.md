# OAP Home Node

Home Node is a first-party runtime role, not a single device type.

The same bounded runtime may run on:
- Android phone or tablet through Termux.
- Linux desktop or laptop.
- macOS desktop or laptop.
- Windows desktop or laptop.

Each Home Node uses the same two-worker contract:

1. `mission_control.organism_worker` — durable heartbeat, health, recovery and governed organism cycles.
2. `scripts/oap_home_node_inference_worker.py` — outbound-only first-party SMI inference through local Ollama.

Both workers are supervised by `scripts/oap_home_node_supervisor.py`. No inbound inference port is required. Human Authority remains final and consequential execution disabled.

## One readiness contract

A device counts as a ready Home Node only when:
- the supervisor is running;
- the organism worker is running;
- the inference worker is running;
- the bridge secret is configured;
- the durable organism runtime reports `ready=true`;
- production SMI reports `worker_recently_seen=true` and `first_party_inference_ready=true`.

The device may be a phone, tablet, laptop or desktop. The proof standard does not change by platform.

## Android phone or tablet

Use the Termux scripts:
- `scripts/termux_home_node_setup.sh`
- `scripts/termux_home_node_run.sh`
- `scripts/termux_home_node_status.sh`

The Termux launcher adds Android wake-lock handling, then delegates runtime supervision to the canonical Python supervisor.

## Linux or macOS

Provide the private environment variables in `$HOME/.config/oap/home-node.env`, activate the repository virtual environment, then run:

```bash
~/on-any-postcode/scripts/home_node_run.sh
```

For status:

```bash
~/on-any-postcode/.venv/bin/python ~/on-any-postcode/scripts/oap_home_node_status.py
```

## Windows

Provide the private environment variables either in the current user environment or in:

```text
%USERPROFILE%\.config\oap\home-node.ps1
```

Then run:

```powershell
& "$HOME\on-any-postcode\scripts\home_node_run.ps1"
```

For status:

```powershell
& "$HOME\on-any-postcode\.venv\Scripts\python.exe" "$HOME\on-any-postcode\scripts\oap_home_node_status.py"
```

## Required private configuration

Each device needs:
- production Neon PostgreSQL credential;
- Home Node bridge secret matching the SMI service;
- local Ollama endpoint/model configuration where non-default;
- a reviewed repository revision.

Secrets stay local to the device and must not be committed.

## Multi-device operation

More than one Home Node may be online. The bridge/job layer decides which available worker receives a bounded inference job; device presence does not grant additional authority.

A phone can be the active node while a desktop is offline, and the desktop can take over when available. Availability is evidence-driven, not device-priority mythology.

## Locked boundaries

Home Node does not grant deploy, publish, payment, money-transfer, role/permission, carrier-switch, migration or other consequential authority. It does not self-approve improvements. It does not self-update from GitHub.
