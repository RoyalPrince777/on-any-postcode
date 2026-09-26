# OAP Host Core

OAP Host is the first-party hosting control plane for OAP services.

It is **not** a claim that OAP already owns or operates all physical hosting.
The current slice defines the canonical service inventory, self-hosting evidence
requirements, STOP/human-authority boundaries, and deploy/rollback proof gate.

Green requires explicit evidence for:

- OAP host node identity
- self-hosted infrastructure
- self-hosted data custody
- controlled network egress
- first-party observability
- proven backup/restore
- supply-chain attestation
- proven deploy + rollback path

External hosting may remain a temporary provider during migration, but it never
counts as proof that OAP Host is self-hosted.

Canonical services currently include the public app, SMI, OAP Route Core
regional shards, PostgreSQL, object storage and TURN.

Consequential deploy/rollback execution remains disabled in this slice.
