# SMI exact character — recovered private source evidence (2026-09-22)

**Read-only evidence recovery; not animation certification.** This record
does not contain or publish the private image, masks, layer PNGs or motion
frames. Original bytes remain in private custody. The existing draft PR #484
and its parent #483 are preserved.

## Original and recovered artifacts

- Exact source: original user-owned `3325.png`, 1536 × 1024, SHA-256
  `f9503174f6f18b815f1c73e24faff3b4966c2e1fbae8d20a8d2bcc22e4a84a4b`;
  identical SHA expected by `static/oap/smi_live_chat_dashboard.jpg`.
- Recovered private `SMI-private-layer-review-v01.zip` contains seven
  `layers/*.png`, seven `masks/*.png`, manifest, geometry and review note.
  Independently inspected recovered bytes: 7/7 layer PNG digests match
  manifest and every selected visible layer RGB pixel matches the original.
  The archive's own review record reports source-pixel lineage and
  landmark registration passed, with anatomy/identity quality review pending.
- `SMI-recovered-seven-draft-masks.zip` contains seven nonempty masks;
  manifest explicitly says `DRAFT_REQUIRES_FOUNDER_REVIEW`,
  `animation_active:false`, `human_anatomy_review:pending`.
- `SMI-private-source-motion-candidates-v01.zip` has ten transparent,
  source-pixel head/eye candidate frames, five per region.
  Its manifest declares `audio_used:false`, `approved_by_founder:false`,
  `motion_proven:false`, `live_connected:false`, and
  `accurate_lip_sync_proven:false`.

**Correction to earlier shorthand:** The approved original and genuine
source-derived *draft* layer bytes are not missing. What remains missing is
Founder-reviewed usable anatomy/occlusion/hidden-region geometry, genuine
speech alignment, witnessed continuous live motion and physical Android STOP.

## Exact-head security issue

PR #484 governed CI #35753399165 passed, including 1,580 Python
regressions, Node frame/STOP checks and the real Chromium private
pixel-frame export. Separate code-scanning run #35753400790 failed before
review: its log reports `SessionModelError` /
`CAPIError: 400 The requested model is not supported` while creating its
Copilot security-review session. This is not a code-vulnerability finding
and does not count as a completed security review.

## Safe NEXT

1. Review the **already recovered** seven masks against original SMI anatomy
   and occlusion; retain draft flags until real human acceptance.
2. Preserve the one first-party character/controller, original artwork,
   Chat/Plus/upload/STOP/HRM, privacy and no visible Live Status.
3. Reuse the detached no-text-guess audio-clock viseme bridge; a real
   decoded-audio aligner and witnessed played-audio sync are still required.
4. Repair or independently complete security review without substituting
   a fake CI green; capture Android STOP, rollback and Founder Final.

No copied private asset, new avatar, extra brain, merge, activation or
deployment is authorised by this evidence note.
