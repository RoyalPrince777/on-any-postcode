# SMI Command Centre — five-item master blueprint

**Scope:** Independently verified mobile controls; genuine movement of the exact approved original character; accurate lip-sync driven by audio actually played; physical Android STOP timing; independent release review. Nothing else is in scope. This document is the implementation and acceptance blueprint, **not a certificate of completion**, deployment instruction, new demo stage, or assertion of physical testing.

**Source of truth:** Founder/Human Authority final. Proof before execution; verification before sharing; audit before automation. Upgrade-only, first-party, least privilege, private/public separation, no invented permission, no external telemetry, no unreviewed asset replacement. Preserve STOP, Plus/upload, HRM, original artwork, existing first-party systems and the working chat layout.

## Exact source, existing contracts and boundary

- PR #516: https://github.com/RoyalPrince777/on-any-postcode/pull/516, originally based on `8499c6b652cfa4d580e3cb0a4dc7b871b888e626`. Fetch the *current* PR and `main` heads before acting; do not freeze the document's commit IDs into an action.
- Exact approved visible image: `static/oap/smi_live_chat_dashboard.jpg`, SHA-256 `f9503174f6f18b815f1c73e24faff3b4966c2e1fbae8d20a8d2bcc22e4a84a4b`. Never overwrite or silently substitute it. Verify bytes before and after changes. Preserve original identity, pose, proportions, clothing, texture and artwork.
- `mission_control/static/smi_canonical_controller.js`: canonical stream completion, mobile controls, STOP/retry and browser-voice lifecycle; STOP is Human Authority.
- `mission_control/static/smi_exact_character_rig.js`: **design-only and fail-closed**. It emits no real frames; no motion or production permission may be inferred from the seven layer names.
- `oap/smi/character_rig_assets.py`, geometry/lineage/registration contracts: private asset verification only; bytes verified are not visual, motion or Founder approval.
- `mission_control/smi_real_reply_motion_bridge.js`: isolated candidate **not loaded on the live page**. Requires integrity-bound decoded-audio alignment; text-predicted mouth shapes and browser speech lifecycle events are not accurate lip-sync evidence.
- `mission_control/smi_android_motion_evidence_gate.js`: evaluates externally obtained Human-observed Android receipts, does not collect measurements or grant production.
- Recovery reference: `docs/SMI_FIVE_ITEM_RECOVERY_PR516.md`. No force pushes, broad revert of `main`, accidental inclusion of unrelated newer work, or production writes.

## Single acceptance ledger — five items, never inferred from CI

| Item | Exact implementation target | Independent acceptance artifact | Fail-closed blocker |
| --- | --- | --- | --- |
| 1. Mobile controls | Founder-authenticated Android chat: Plus/open/close; approved upload/camera and attachment acknowledgement; mic permission/start/stop; send; thinking-level selection; visible STOP and explicit resume; live off/on; no stale callbacks or duplicate completion/receipts. Original controls remain accessible and operable. | Device model, Android/Chrome version, exact tested commit and URL, authenticated/consent context without secrets, screen recording or signed human test notes, input and outcome for each control, errors and retest after STOP/background/reload, two-device or independent reviewer confirmation. | Browser-only fixture, screenshot of buttons, CSS assertion, or missing end-to-end upload/STOP proof. |
| 2. Original character movement | Genuine source-derived seven-segment approved rig with eyes, head, breathing/torso, mouth, face, hands and upper body; actual temporally varied frames, layer depth/occlusion, deterministic STOP freeze and reduced-motion static fallback. No still-photo CSS wobble advertised as real motion. | Privately stored source/layer byte hashes and provenance, independent visual comparison with exact approved portrait, footage/frame evidence of real mouth/eyes/head/hands/breathing motion and cessation, explicit Founder visual approval. | Missing source-approved deformable layers, rig outputs `null`, look-alike substitution, unapproved private asset publication. |
| 3. Accurate lip-sync | First-party audio playback path with **decoded reply audio** (not only `SpeechSynthesisUtterance` callbacks); hash-bound phoneme/viseme timeline for that same audio; drive mouth frames from actually playing media/audio clock; silence, pause, end, error, seek/restart and STOP behave correctly. | Audio SHA-256, decoded duration and alignment provenance, visual capture plus played-audio clock trace, bounded maximum audio-to-mouth delta <=80 ms under the current candidate gate, observed silence and interruption, independently checked sample. Store no transcript/raw audio in public telemetry. | Text-predicted visemes, wall-clock alone, fake/synthetic approval fields, clock reset by duplicate start, alignment from a different audio asset, browser speech events taken as decoded audio. |
| 4. Physical Android STOP | Human STOP immediately invalidates in-flight stream, voice, playback, live capture, scheduling and motion; stale events cannot restart it; explicit valid Human action alone resumes. STOP works foreground/background/permission failure and during audio and upload. | **Physical** device identity, tested commit, pointer/tap and acknowledgement timestamps from device instrumentation, observed audio and motion stopped, repeated latency samples including slowest acknowledgement <=50 ms, background and replay tests, fresh independent Human observation. | Simulated timestamps, a self-declared receipt without device evidence, one passing unit test, missing physical audio/motion cessation. |
| 5. Independent release review | Verify exact candidate against freshly fetched `main`, CI, protection and privacy, assets, authenticated Android UX and four preceding acceptance artifacts; release gate is distinct from Founder decision. | Recorded independent reviewer identity and signed/traceable review verdict, addressed findings, exact SHA and CI run, conflict and scope assessment, release candidate/rollback plan, explicit separate Founder Final. | Unsupported review model, queued/failed review run, missing live Android evidence, incomplete independent visual approval, false green. |

**Five-item percentage rule:** independently accepted artifacts / 5, multiplied by 100. Do not assign subjective per-feature percentages or claim that passing tests means mobile or animation acceptance. A release cannot pass while any required item is unverified.

## Locked four steps (gate labels, not implementation-completion percentages)

**25% — Rollback / Recovery.** Confirm exact PR/main/base, bounded diff, original artwork hash, fail-closed design rig, preserved controls, isolated rollback reference and governed CI. This closes only source-level recovery, never physical acceptance. Do not overwrite newer `main` changes.

**50% — Runtime Guard.** Preserve canonical controller and single completion owner, owner-scoped receipts, STOP invalidation, explicit resume, Plus/upload, mic and stale-callback guards. Run regressions. Independently execute Android controls and record the device acceptance artifact; until then the full runtime gate stays yellow even if code checks pass.

**75% — Aegis Isolation / Recovery.** Privately approve genuine source-derived layers; establish rendered motion and decoded played-audio visemes, timing/identity and privacy; measure <=50 ms STOP physically including background and stale-event suppression. Do not connect the candidate to the live page before the independent visual, audio, security and STOP proofs. The bridge/receipt gates cannot manufacture observations.

**100% — Green Gate + Founder Final.** Re-fetch exact releasable commit, `main`, branch protection and independent review; independently validate all five artifacts and seven stars, CI, complete release rollback and production boundaries. Ask the Founder to approve the specific audited release action separately. No merge, migration, live database write or deploy merely because this blueprint or a prior 🟢 exists.

## Seven-star release checks

1. **Truth:** exact commits, CI log and scope evidence; label source tests vs physical observations.
2. **Identity:** unchanged original artwork hash and independently approved private rig lineage.
3. **Guardian:** founder-only controls, consent, youth/privacy boundaries and explicit Human STOP.
4. **SMI intelligence:** single canonical completion, real audio identity and correct stale-state handling.
5. **Functionality:** real Android Plus/upload, mic, send, thinking, STOP and resumed-work outcomes.
6. **Resilience:** background, interruption, failure, pause, reduced motion, rollback and repeated STOP timing.
7. **Audit / Human Authority:** independent review, dated per-item receipts, exact release candidate and separate Founder Final.

A star is green only if its own evidence is recorded for the *current* commit/device. Yellow = incomplete; red = observed failure; grey = untested. 21 signals may expand these checks only with a stated denominator and actual observations, never a fabricated 21/21.

## Concrete work order and evidence capture

1. Capture exact head, CI and rollback boundary on the isolated branch; maintain original image SHA checks in CI.
2. Exercise mobile controls on physical Android using a controlled Founder session; record exact failing control paths and fix them without changing unrelated systems.
3. Privately establish and visually approve **true** segmented layers from the approved portrait. If unavailable, stop with a clear blocker rather than generate substitutes or enable the design-only rig.
4. Implement real frame emission in the approved rig and first-party decoded audio delivery/alignment; verify media-clock-driven visemes and fail-closed STOP. Do not claim production motion while the live rig is design-only.
5. Capture physical Android STOP latency and audio/motion cessation across repeated scenarios; independently validate source hashes, timing and authenticity of the receipt.
6. Complete a functioning independent security/release review. A repeated unsupported-model AI job is **not** a security verdict: resolve reviewer tooling or obtain equivalent genuine independent review, and record which gate still lacks evidence.
7. Only then present exact scope, commit, CI, five artifacts, seven stars, rollback and a separate Founder release decision.

**Current baseline at blueprint authoring (reverify):** PR #516 draft and unmerged at `47356aee5fb31cdaf8fb93d0a2cd109de3d4c4c9`; governed CI #2454 passed 1,638 tests; scanning #873 did not run successfully because its requested model was unsupported; `main` was `fb626c81f202d83c5e536c3ec2da10dad28a5087`. No physical Android or genuine source-approved rig acceptance is asserted by this document. Current completion of all five independently accepted features was 0/5 at that baseline.

**Release rule:** preserve existing first-party systems and original artwork. No fake green, no silent removals, no demos as production, no self-issued proof, no unreviewed permissions and no production action without verified release gates **and separate Founder Final**.
