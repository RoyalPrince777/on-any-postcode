# Exact approved SMI character — motion media handoff

This release is a **fail-closed asset player**, not a generated rig, full-body animation, or proof that motion media already exists. Its purpose is to prevent replacing the Founder-approved character with a different synthetic look while preparing genuine first-party animation.

## Required media before enabling

Supply three individually Founder-approved short, loopable whole-scene videos (or a reviewed source rig and resulting exports) for **listening, thinking, speaking**. Each must use the exact original approved `static/oap/smi_global_intelligence_command_centre.png` as its visual source, with identical frame size, framing, static labels, and background. Only original character facial features/body/hair may move. A looped "speaking" clip is animation; it is **not phoneme-accurate lip-sync** without actual time-aligned audio/viseme data. Never infer motion from baked image numbers or replace the avatar with unrelated generations.

Store reviewed clips as first-party `/static/oap/smi_motion/<name>.webm` (or `.mp4` where supported). Preserve the original PNG and its existing release hash. No third-party CDNs or telemetry. Decode locally in the signed-in Founder browser; never upload audio, video or private transcripts to third parties.

After visual Founder approval, explicitly set `OAP_SMI_UI.approvedMotionClips` to an object keyed by `listening`, `thinking`, `speaking`; each entry has only `{url: "/static/oap/smi_motion/<name>.webm", sha256: "<64 lowercase hex>"}`. Do **not** set these keys until the bytes have been added, checked against the original artwork, SHA-256 checksummed, CI-tested and approved.

## Fail-closed behavior

No config, missing media, unsupported codec, mismatched hash, cross-origin URL, fetch error, oversized clip, autoplay refusal, STOP/paused/ready, or reduced-motion preference must keep the original still and existing state-linked ambient response. Media cannot grant execution or Green Gate authority, cannot access mic/camera, and cannot change Founder password, SMI brain, Chat, Tools or Human STOP.

The media player will only appear inside the approved **Command Centre scene**. It does not yet provide full-screen Live SMI motion, camera-aware gaze, true synchronous lip-sync or body-tracked gestures. Those require distinct source assets and runtime/device evidence. Do not certify these features from the mere presence of a clip.

Release acceptance: exact-approved-art visual comparison (desktop + signed-in Android); real listening/thinking/speaking transitions; STOP/pause immediately hide media; reduced-motion fallback; low-bandwidth failure; mobile CPU/battery/thermal budget; no third-party requests or secrets; no duplicate SMI controller; Founder final after verified evidence.
