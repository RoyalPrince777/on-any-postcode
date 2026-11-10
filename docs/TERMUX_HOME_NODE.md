# OAP Termux Home Node

For the device-agnostic Home Node contract covering Android phone/tablet, Linux, macOS and Windows, see `docs/HOME_NODE.md`.

The Termux Home Node is the zero-hosting-cost continuous runtime for two bounded first-party workers:

- `mission_control.organism_worker` for heartbeat, health and governed organism cycles.
- `scripts/oap_home_node_inference_worker.py` for outbound-only SMI inference through local Ollama.

The inference worker opens no inbound port. It polls the private OAP bridge over HTTPS, runs the job locally, and returns only the bounded result. Human Authority remains final and consequential execution disabled.

## What stays locked

The Home Node does not enable deployment, publication, payment capture, money transfer, driver dispatch, permissions/roles changes, production migrations, eSIM activation, carrier switching, public precise tracking, or self-application of improvements.

The node deliberately does **not** auto-pull GitHub changes. Updating the running revision remains an explicit Human Authority action.

## Requirements

- Android device with Termux installed from a supported source.
- Termux:Boot installed from the same signing/source family and opened once.
- Reliable power and network connection.
- Android battery usage for Termux and Termux:Boot set to Unrestricted where the device exposes that setting.
- Production Neon PostgreSQL connection URL.
- The same Home Node bridge secret configured on the SMI service.
- Local Ollama running with the configured OAP model.

The database URL and bridge secret are entered interactively in Termux and stored only in `$HOME/.config/oap/home-node.env` with mode `600`; they must never be committed to GitHub.

Termux:Boot executes scripts placed in `~/.termux/boot/`. Its official documentation recommends `termux-wake-lock` for workloads that should continue while the device sleeps.

## First setup

From Termux:

```bash
pkg install -y git

git clone https://github.com/RoyalPrince777/on-any-postcode.git ~/on-any-postcode
cd ~/on-any-postcode
bash scripts/termux_home_node_setup.sh
```

The setup script installs dependencies, creates the virtual environment, securely prompts for the production database URL and Home Node bridge secret, creates the boot entry, and does not start any consequential action.

Then start the node immediately:

```bash
~/on-any-postcode/scripts/termux_home_node_run.sh
```

Termux:Boot will start the node on later device boots.

## Verify

In another Termux session:

```bash
~/on-any-postcode/scripts/termux_home_node_status.sh
```

A genuinely green runtime requires all of:

- `home_node_process=running`
- `organism_worker=running`
- `inference_worker=running`
- `bridge_secret_configured=true`
- runtime JSON containing `"worker_fresh": true` and `"ready": true`
- production SMI reporting `worker_recently_seen=true` and `first_party_inference_ready=true`

The authoritative runtime heartbeat is persisted in Neon, not inferred from the local process alone.

Logs are written under:

```text
~/.local/state/oap-home-node/
```

## Stop

Find the runner PID from `~/.local/state/oap-home-node/lock/pid` and send TERM. The runner forwards termination to the bounded worker so it can drain its current job and write its final STOPPED heartbeat.

```bash
kill -TERM "$(cat ~/.local/state/oap-home-node/lock/pid)"
```

## Governed update

The runtime never changes its own code. To move to a newer reviewed `main` revision:

```bash
cd ~/on-any-postcode
git fetch origin main
git checkout main
git pull --ff-only origin main
.venv/bin/python -m pip install -r requirements.txt
kill -TERM "$(cat ~/.local/state/oap-home-node/lock/pid)" 2>/dev/null || true
scripts/termux_home_node_run.sh
```

Only perform this after the target `main` revision has passed the governed checks you intend to deploy.
