# SMI Body 8–14 — private seven-layer asset evidence gate

**Approved source:** `static/oap/smi_live_chat_dashboard.jpg` at
SHA-256 `f9503174f6f18b815f1c73e24faff3b4966c2e1fbae8d20a8d2bcc22e4a84a4b`.
Preserve the approved artwork, existing first-party character, state bus and
fail-closed passive contract merged from PR #462.

## What this addition does

`oap.smi.character_rig_assets.inspect_assets(manifest, private_root)` performs
**offline, read-only byte checks** of exactly seven private PNG layers: eyes,
head, breathing, mouth visemes, face, hands, upper body. It checks exact source
identity, all seven manifest entries, basename-only filenames, actual file
SHA-256, non-symlink files, bounded dimensions and decoded alpha PNG bytes.
Only a bounded verdict is returned. Private file paths and image bytes never
enter a public route, JS bundle, visible dashboard, telemetry or HRM.

`docs/SMI_RIG_PRIVATE_ASSET_MANIFEST.example.json` deliberately supplies
`null` for all layers. There are no approved segmented files in this PR.
No claimed `rig_enabled`, `motion_proven` or `founder_approved` manifest flag
grants approval. Even seven byte-valid layers return
`bytes_verified_only_requires_independent_rig_proofs`, with `active=false`,
`motion_proven=false` and `human_authority_approved=false`.

## Additional, independent body proof needed before a real rig

1. Founder approves true segmented layers derived from the exact original
   without replacement or identity alteration; record source and layer
   provenance privately.
2. Prove identifiable eyes, head, torso, mouth/face and both hands map to real
   deformable layers with consistent occlusion, alignment and depth. A cropped
   still or seven alpha masks alone is not enough.
3. Capture motion/timing evidence for gaze, breathing, expression, gestures and
   audio-aligned phoneme-to-viseme sequencing. Verify lip timing against audio
   actually played, including silence, pause, interruption and STOP.
4. Verify STOP immediately prevents *all* voice/motion paths; reduced-motion
   accessibility preserves an understandable still-image experience.
5. Test real Founder-only Android layout, local consent, data retention,
   resource budgets and privacy. Human Authority final before activation.

Do not copy any images into an unprotected `static/` path merely to make the
verifier green. Keep asset storage private and review delivery/auth
separately. No tool may infer liveness from these byte checks.

## Status boundary

This is an **upgrade-only evidence tool**, not a new brain, agent, database,
approval authority or fifth stage. The locked 25/50/75/100% law is unchanged.
Existing approved portrait remains visible and no character animation is
enabled or deployed by this file. The separate SMI chat/Founder PR #459 is
not merged as part of this scope.
